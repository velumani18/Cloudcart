"""Order processing, inventory management, and lifecycle event orchestration."""
import random
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.models import (
    Order,
    OrderItem,
    OrderStatus,
    VALID_ORDER_TRANSITIONS,
    Product,
    Customer,
    utc_now,
)
from backend.repositories.order_repository import OrderRepository
from backend.repositories.product_repository import ProductRepository
from backend.repositories.customer_repository import CustomerRepository
from backend.services.email_templates import (
    render_order_placed_template,
    render_payment_confirmed_template,
    render_order_packed_template,
    render_order_shipped_template,
    render_order_delivered_template,
    render_order_cancelled_template,
    render_refund_processed_template,
)
from backend.services.outbox_service import enqueue_outbox_event


class OrderService:
    """Core e-commerce order business logic."""

    @staticmethod
    def create_order(
        db: Session,
        customer_id: str,
        items: List[Dict[str, Any]],
        shipping_address: str,
        payment_method: str = "simulated_card",
    ) -> Tuple[Order, List[str]]:
        """
        Transactionally create an order, reserve stock, and enqueue cloud notifications.
        Returns (order, [outbox_event_ids]).
        """
        customer = CustomerRepository.get_by_id(db, customer_id)
        if not customer:
            raise ValueError(f"Customer with ID '{customer_id}' does not exist.")

        if not items:
            raise ValueError("Order must contain at least one item.")

        # 1. Validate stock and prices for all items
        order_items_data = []
        total_amount = 0.0

        for it in items:
            pid = it.get("product_id")
            qty = it.get("quantity", 1)
            if qty <= 0:
                raise ValueError("Item quantity must be greater than zero.")

            product = db.query(Product).filter(Product.id == pid).first()
            if not product or not product.is_active:
                raise ValueError(f"Product '{pid}' is unavailable or inactive.")

            if product.stock_quantity < qty:
                raise ValueError(
                    f"Insufficient stock for '{product.name}'. Requested {qty}, but only {product.stock_quantity} available."
                )

            subtotal = round(product.price * qty, 2)
            total_amount = round(total_amount + subtotal, 2)

            # Decrement stock transactionally
            product.stock_quantity -= qty

            order_items_data.append({
                "product_id": product.id,
                "product_name": product.name,
                "unit_price": product.price,
                "quantity": qty,
                "subtotal": subtotal,
            })

        # 2. Create Order entity
        import uuid
        order_number = OrderRepository.generate_order_number(db)
        simulated_pay_ref = f"SIM-PAY-{random.randint(100000, 999999)}"

        order = Order(
            id=str(uuid.uuid4()),
            order_number=order_number,
            customer_id=customer.id,
            status=OrderStatus.PLACED.value,
            total_amount=total_amount,
            shipping_address=shipping_address.strip(),
            payment_method=payment_method,
            payment_reference=simulated_pay_ref,
        )
        db.add(order)
        db.flush()

        # 3. Create OrderItems
        for o_data in order_items_data:
            item = OrderItem(
                order_id=order.id,
                product_id=o_data["product_id"],
                product_name=o_data["product_name"],
                unit_price=o_data["unit_price"],
                quantity=o_data["quantity"],
                subtotal=o_data["subtotal"],
            )
            db.add(item)

        # 4. Record initial status history
        OrderRepository.add_status_history(
            db=db,
            order_id=order.id,
            to_status=OrderStatus.PLACED.value,
            from_status=None,
            notes="Order placed by customer via checkout.",
            changed_by=customer.name,
        )

        event_ids: List[str] = []

        # 5. Enqueue automatic 'order_placed' cloud notification in Transactional Outbox
        order_date_str = order.created_at.strftime("%Y-%m-%d %H:%M UTC") if order.created_at else "Today"
        placed_tmpl = render_order_placed_template(
            customer_name=customer.name,
            order_number=order.order_number,
            items=order_items_data,
            total_amount=order.total_amount,
            order_date_str=order_date_str,
            shipping_address=order.shipping_address,
        )
        placed_event = enqueue_outbox_event(
            db=db,
            recipient=customer.email,
            event_type=placed_tmpl["event_type"],
            subject=placed_tmpl["subject"],
            body=placed_tmpl["body"],
            order_id=order.id,
            customer_id=customer.id,
        )
        event_ids.append(placed_event.id)

        # 6. Commit atomic transaction (status is PLACED, single order_placed event enqueued)
        db.commit()
        db.refresh(order)

        return order, event_ids

    @staticmethod
    def update_order_status(
        db: Session,
        order_id: str,
        to_status: str,
        notes: Optional[str] = None,
        tracking_number: Optional[str] = None,
        cancellation_reason: Optional[str] = None,
        changed_by: str = "admin",
    ) -> Tuple[Order, Optional[str]]:
        """
        Transition order through its lifecycle. Enforces valid state transitions
        and automatically enqueues the corresponding business event notification.
        Returns (order, outbox_event_id_or_None).
        """
        order = OrderRepository.get_order(db, order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        current_status = order.status
        target_status = to_status.lower().strip()

        # Check idempotent no-op
        if current_status == target_status:
            return order, None

        # Validate transition against strict lifecycle policy
        allowed = VALID_ORDER_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise ValueError(
                f"Invalid order status transition from '{current_status}' to '{target_status}'. "
                f"Allowed transitions: {', '.join(allowed) if allowed else 'None (Terminal state)'}."
            )

        customer = order.customer
        recipient_email = customer.email if customer else None

        # Handle cancellation stock restoration
        if target_status == OrderStatus.CANCELLED.value:
            for item in order.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock_quantity += item.quantity
            order.cancellation_reason = cancellation_reason or notes or "Order cancelled by administrator."

        if tracking_number:
            order.tracking_number = tracking_number

        # Update order status
        order.status = target_status
        order.updated_at = utc_now()

        # Record history
        OrderRepository.add_status_history(
            db=db,
            order_id=order.id,
            to_status=target_status,
            from_status=current_status,
            notes=notes,
            changed_by=changed_by,
        )

        outbox_event_id = None
        if recipient_email:
            tmpl = None
            if target_status == OrderStatus.PAYMENT_CONFIRMED.value:
                tmpl = render_payment_confirmed_template(
                    order_number=order.order_number,
                    amount_paid=order.total_amount,
                    payment_reference=order.payment_reference or f"SIM-PAY-{order.order_number}",
                    is_simulated=True,
                )
            elif target_status == OrderStatus.PACKED.value:
                tmpl = render_order_packed_template(order.order_number)
            elif target_status == OrderStatus.SHIPPED.value:
                tmpl = render_order_shipped_template(order.order_number, tracking_number=order.tracking_number or "")
            elif target_status == OrderStatus.DELIVERED.value:
                tmpl = render_order_delivered_template(order.order_number)
            elif target_status == OrderStatus.CANCELLED.value:
                tmpl = render_order_cancelled_template(order.order_number, reason=order.cancellation_reason or "")
            elif target_status == OrderStatus.REFUND_PROCESSED.value:
                tmpl = render_refund_processed_template(order.order_number, refund_amount=order.total_amount)

            if tmpl:
                outbox_event = enqueue_outbox_event(
                    db=db,
                    recipient=recipient_email,
                    event_type=tmpl["event_type"],
                    subject=tmpl["subject"],
                    body=tmpl["body"],
                    order_id=order.id,
                    customer_id=order.customer_id,
                )
                outbox_event_id = outbox_event.id

        db.commit()
        db.refresh(order)

        return order, outbox_event_id

    @staticmethod
    def get_order(db: Session, order_id: str) -> Optional[Order]:
        return OrderRepository.get_order(db, order_id)

    @staticmethod
    def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
        return OrderRepository.get_order_by_number(db, order_number)

    @staticmethod
    def list_orders(
        db: Session,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Order]:
        return OrderRepository.list_orders(db, customer_id=customer_id, status=status, limit=limit)
