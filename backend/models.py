"""SQLAlchemy ORM models for CloudCart event-driven e-commerce platform."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from backend.database import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


class OrderStatus(str, Enum):
    """Lifecycle stages for an e-commerce order."""
    PLACED = "placed"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUND_PROCESSED = "refund_processed"


# Strictly defined business lifecycle transitions
VALID_ORDER_TRANSITIONS: Dict[str, List[str]] = {
    OrderStatus.PLACED.value: [
        OrderStatus.PAYMENT_CONFIRMED.value,
        OrderStatus.CANCELLED.value,
    ],
    OrderStatus.PAYMENT_CONFIRMED.value: [
        OrderStatus.PACKED.value,
        OrderStatus.CANCELLED.value,
    ],
    OrderStatus.PACKED.value: [
        OrderStatus.SHIPPED.value,
        OrderStatus.CANCELLED.value,
    ],
    OrderStatus.SHIPPED.value: [
        OrderStatus.DELIVERED.value,
        OrderStatus.CANCELLED.value,
    ],
    OrderStatus.DELIVERED.value: [
        OrderStatus.REFUND_PROCESSED.value,
    ],
    OrderStatus.CANCELLED.value: [
        OrderStatus.REFUND_PROCESSED.value,
    ],
    OrderStatus.REFUND_PROCESSED.value: [],
}


class NotificationEventStatus(str, Enum):
    """Transactional Outbox notification statuses."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"       # AWS HTTP 202 Accepted for cloud processing
    REJECTED = "REJECTED"       # AWS HTTP 400 Bad Request
    FAILED = "FAILED"           # AWS HTTP 5xx or network connection failure
    UNCERTAIN = "UNCERTAIN"     # Timeout where request may have reached AWS


class Customer(Base):
    """E-commerce customer account."""
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    notifications = relationship("NotificationOutbox", back_populates="customer")


class Product(Base):
    """Product catalog item."""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    """Customer purchase order."""
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    status = Column(String(50), default=OrderStatus.PLACED.value, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(Text, nullable=False)
    payment_method = Column(String(50), default="simulated_card", nullable=False)
    payment_reference = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
    )
    notifications = relationship("NotificationOutbox", back_populates="order")


class OrderItem(Base):
    """Line item in a customer order."""
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class OrderStatusHistory(Base):
    """Audit log of order status changes."""
    __tablename__ = "order_status_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    changed_by = Column(String(100), default="system", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    order = relationship("Order", back_populates="status_history")


class NotificationOutbox(Base):
    """Transactional Outbox for event-driven cloud email notifications."""
    __tablename__ = "notification_outbox"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(
        String(50),
        default=NotificationEventStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    external_http_status = Column(Integer, nullable=True)
    notification_id = Column(String(255), nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    order = relationship("Order", back_populates="notifications")
    customer = relationship("Customer", back_populates="notifications")


# Composite indexes for queries
Index("ix_outbox_status_created", NotificationOutbox.status, NotificationOutbox.created_at)
Index("ix_orders_customer_created", Order.customer_id, Order.created_at)
