"""Centralized, reusable email templates for CloudCart business events.
Generates plain-text bodies matching the AWS API Gateway notification contract.
"""
from typing import Dict, Any, List


def render_user_registered_template(customer_name: str, email: str) -> Dict[str, str]:
    """Event: user_registered."""
    subject = "Welcome to CloudCart!"
    body = (
        f"Hi {customer_name},\n\n"
        "Welcome to CloudCart — your modern destination for premium electronics, audio, and gadgets!\n\n"
        f"Your account ({email}) is now active. You can browse our catalog, manage your shopping cart, "
        "and track your orders in real time.\n\n"
        "Happy shopping,\n"
        "The CloudCart Team"
    )
    return {
        "event_type": "user_registered",
        "subject": subject,
        "body": body,
    }


def render_order_placed_template(
    customer_name: str,
    order_number: str,
    items: List[Dict[str, Any]],
    total_amount: float,
    order_date_str: str,
    shipping_address: str,
) -> Dict[str, str]:
    """Event: order_placed."""
    subject = "Your CloudCart order has been confirmed."

    items_lines = []
    for it in items:
        p_name = it.get("product_name", "Item")
        qty = it.get("quantity", 1)
        sub = it.get("subtotal", 0.0)
        items_lines.append(f"  • {p_name} x{qty} — ${sub:.2f}")

    items_block = "\n".join(items_lines) if items_lines else "  • No items"

    body = (
        f"Dear {customer_name},\n\n"
        f"Thank you for your purchase! Your order {order_number} has been received and confirmed.\n\n"
        f"Order Summary:\n"
        f"----------------------------------------\n"
        f"Order Number: {order_number}\n"
        f"Order Date: {order_date_str}\n"
        f"Delivery Address: {shipping_address}\n\n"
        f"Items Ordered:\n"
        f"{items_block}\n\n"
        f"Total Amount: ${total_amount:.2f}\n"
        f"----------------------------------------\n\n"
        f"You can track the live progress and status of your shipment anytime at:\n"
        f"http://localhost:8501/Track_Order?order={order_number}\n\n"
        f"Best regards,\n"
        f"CloudCart Operations"
    )
    return {
        "event_type": "order_placed",
        "subject": subject,
        "body": body,
    }


def render_payment_confirmed_template(
    order_number: str,
    amount_paid: float,
    payment_reference: str,
    is_simulated: bool = True,
) -> Dict[str, str]:
    """Event: payment_confirmed."""
    subject = "Payment received for your order."
    note = " [Simulated Sandbox Transaction]" if is_simulated else ""
    body = (
        f"Payment Confirmation{note}\n\n"
        f"We have successfully received payment for order {order_number}.\n\n"
        f"Transaction Details:\n"
        f"----------------------------------------\n"
        f"Order Number: {order_number}\n"
        f"Payment Status: Confirmed / Paid\n"
        f"Amount Paid: ${amount_paid:.2f}\n"
        f"Transaction Reference: {payment_reference}\n"
        f"----------------------------------------\n\n"
        "Our warehouse team is now preparing your items for packaging.\n\n"
        "Thank you for choosing CloudCart!"
    )
    return {
        "event_type": "payment_confirmed",
        "subject": subject,
        "body": body,
    }


def render_order_packed_template(order_number: str) -> Dict[str, str]:
    """Event: order_packed."""
    subject = "Your order is packed."
    body = (
        f"Great news! Your CloudCart order {order_number} has been inspected, packed, "
        "and is ready at our fulfillment center for courier pickup.\n\n"
        "You will receive a shipment notification with tracking details as soon as the package departs.\n\n"
        "CloudCart Fulfillment Team"
    )
    return {
        "event_type": "order_packed",
        "subject": subject,
        "body": body,
    }


def render_order_shipped_template(order_number: str, tracking_number: str = "") -> Dict[str, str]:
    """Event: order_shipped."""
    subject = "Your order has been shipped."
    track_info = f"Carrier Tracking Number: {tracking_number}\n" if tracking_number else "Tracking: Expedited Ground Delivery\n"
    body = (
        f"Your order {order_number} has been handed over to the courier and is on its way!\n\n"
        f"Shipping Status: In Transit\n"
        f"{track_info}\n"
        f"Track your package live on CloudCart:\n"
        f"http://localhost:8501/Track_Order?order={order_number}\n\n"
        "CloudCart Logistics"
    )
    return {
        "event_type": "order_shipped",
        "subject": subject,
        "body": body,
    }


def render_order_delivered_template(order_number: str) -> Dict[str, str]:
    """Event: order_delivered."""
    subject = "Your order has been delivered."
    body = (
        f"Package Delivered! Your CloudCart order {order_number} has been marked as delivered.\n\n"
        "We hope you enjoy your new products! If you have any questions or require assistance, "
        "please reach out to support@cloudcart.example.com.\n\n"
        "Thank you for shopping with CloudCart!"
    )
    return {
        "event_type": "order_delivered",
        "subject": subject,
        "body": body,
    }


def render_order_cancelled_template(order_number: str, reason: str = "") -> Dict[str, str]:
    """Event: order_cancelled."""
    subject = "Your order has been cancelled."
    reason_line = f"Cancellation Reason: {reason}\n" if reason else "Reason: Customer requested cancellation / Stock reconciliation\n"
    body = (
        f"Notice of Cancellation\n\n"
        f"Your CloudCart order {order_number} has been cancelled.\n\n"
        f"{reason_line}\n"
        "If you were charged for this order, a refund notification will follow once the reversal is processed.\n\n"
        "CloudCart Customer Care"
    )
    return {
        "event_type": "order_cancelled",
        "subject": subject,
        "body": body,
    }


def render_refund_processed_template(order_number: str, refund_amount: float) -> Dict[str, str]:
    """Event: refund_processed."""
    subject = "Your refund has been processed."
    body = (
        f"Refund Confirmation\n\n"
        f"A refund of ${refund_amount:.2f} has been processed for order {order_number}.\n\n"
        "The funds have been returned to your original payment method. Depending on your financial institution, "
        "please allow 3-5 business days for the credit to appear.\n\n"
        "CloudCart Billing Services"
    )
    return {
        "event_type": "refund_processed",
        "subject": subject,
        "body": body,
    }
