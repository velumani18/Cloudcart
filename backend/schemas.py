"""Pydantic validation schemas for CloudCart."""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# --- Customer Schemas ---
class CustomerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Name cannot be empty.")
        return s


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Product Schemas ---
class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=5)
    category: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0.0)
    stock_quantity: int = Field(..., ge=0)
    image_url: Optional[str] = None
    is_active: bool = True


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0.0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    stock_quantity: int
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Order & Checkout Schemas ---
class CartItemInput(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0, description="Quantity to purchase")


class OrderCreateRequest(BaseModel):
    customer_id: str
    items: List[CartItemInput] = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=5)
    payment_method: str = Field("simulated_card", description="Payment option (e.g. simulated_card)")


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderStatusHistoryResponse(BaseModel):
    id: str
    from_status: Optional[str] = None
    to_status: str
    notes: Optional[str] = None
    changed_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    status: str
    total_amount: float
    shipping_address: str
    payment_method: str
    payment_reference: Optional[str] = None
    tracking_number: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdateRequest(BaseModel):
    to_status: str = Field(..., description="Target status in order lifecycle")
    notes: Optional[str] = None
    tracking_number: Optional[str] = None
    cancellation_reason: Optional[str] = None
    changed_by: str = Field("admin", description="Actor performing transition")


# --- Notification Outbox Schemas ---
class NotificationOutboxResponse(BaseModel):
    id: str
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    customer_id: Optional[str] = None
    event_type: str
    recipient: str
    subject: str
    body: str
    status: str
    external_http_status: Optional[int] = None
    notification_id: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Admin Dashboard Stats ---
class AdminDashboardStats(BaseModel):
    total_orders: int
    total_revenue: float
    total_customers: int
    total_products: int
    order_status_counts: Dict[str, int]
    notification_status_counts: Dict[str, int]
    recent_orders: List[OrderResponse] = []
    recent_notifications: List[NotificationOutboxResponse] = []
