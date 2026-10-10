"""Order management and lifecycle transitions router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Order
from backend.schemas import (
    OrderCreateRequest,
    OrderResponse,
    OrderStatusUpdateRequest,
    OrderItemResponse,
    OrderStatusHistoryResponse,
)
from backend.services.order_service import OrderService
from backend.services.outbox_service import dispatch_single_outbox_event

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


def serialize_order(order: Order) -> OrderResponse:
    """Helper to serialize SQLAlchemy Order with relations to Pydantic OrderResponse."""
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        customer_name=order.customer.name if order.customer else None,
        customer_email=order.customer.email if order.customer else None,
        status=order.status,
        total_amount=order.total_amount,
        shipping_address=order.shipping_address,
        payment_method=order.payment_method,
        payment_reference=order.payment_reference,
        tracking_number=order.tracking_number,
        cancellation_reason=order.cancellation_reason,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=it.id,
                product_id=it.product_id,
                product_name=it.product_name,
                unit_price=it.unit_price,
                quantity=it.quantity,
                subtotal=it.subtotal,
            )
            for it in order.items
        ],
        status_history=[
            OrderStatusHistoryResponse(
                id=h.id,
                from_status=h.from_status,
                to_status=h.to_status,
                notes=h.notes,
                changed_by=h.changed_by,
                created_at=h.created_at,
            )
            for h in order.status_history
        ],
    )


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new order (Checkout)",
)
async def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Perform immediate transactional checkout:
    1. Validates stock availability.
    2. Decrements inventory.
    3. Generates unique order number.
    4. Automatically enqueues 'order_placed' and 'payment_confirmed' notifications.
    5. Dispatches notifications immediately to AWS Cloud Notification API (No admin needed!).
    """
    try:
        items_dict = [it.model_dump() for it in payload.items]
        order, event_ids = OrderService.create_order(
            db=db,
            customer_id=payload.customer_id,
            items=items_dict,
            shipping_address=payload.shipping_address,
            payment_method=payload.payment_method,
        )

        # Dispatch cloud email notifications immediately to AWS!
        for eid in event_ids:
            await dispatch_single_outbox_event(eid)

        return serialize_order(order)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List orders",
)
def list_orders(
    customer_id: Optional[str] = Query(None, description="Scope orders to specific customer"),
    status: Optional[str] = Query(None, description="Filter by order lifecycle status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve orders with optional customer or status filtering."""
    orders = OrderService.list_orders(db, customer_id=customer_id, status=status, limit=limit)
    return [serialize_order(o) for o in orders]


@router.get(
    "/{order_identifier}",
    response_model=OrderResponse,
    summary="Get order details by ID or Order Number",
)
def get_order(order_identifier: str, db: Session = Depends(get_db)):
    """Look up an order by its UUID or friendly order number (e.g., ORD-1001-234)."""
    order = OrderService.get_order(db, order_identifier)
    if not order:
        order = OrderService.get_order_by_number(db, order_identifier)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_identifier}' not found.",
        )
    return serialize_order(order)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order lifecycle status",
)
async def update_status(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Transition order through lifecycle stages (packed, shipped, delivered, cancelled, refund_processed).
    Immediately dispatches corresponding cloud notification to AWS API Gateway.
    """
    try:
        updated_order, event_id = OrderService.update_order_status(
            db=db,
            order_id=order_id,
            to_status=payload.to_status,
            notes=payload.notes,
            tracking_number=payload.tracking_number,
            cancellation_reason=payload.cancellation_reason,
            changed_by=payload.changed_by,
        )

        # Dispatch cloud email notification immediately to AWS!
        if event_id:
            await dispatch_single_outbox_event(event_id)

        return serialize_order(updated_order)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
