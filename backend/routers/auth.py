"""Authentication and customer management router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    CustomerRegisterRequest,
    CustomerLoginRequest,
    CustomerResponse,
)
from backend.services.customer_service import CustomerService
from backend.services.outbox_service import dispatch_single_outbox_event

router = APIRouter(prefix="/api/v1/auth", tags=["Customer & Auth"])


@router.post(
    "/register",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer",
)
async def register(
    payload: CustomerRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a customer and immediately trigger the 'user_registered'
    welcome notification to the AWS Cloud Notification Gateway.
    """
    try:
        customer, event_id = CustomerService.register_customer(
            db=db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
            is_admin=False,
        )
        if event_id:
            await dispatch_single_outbox_event(event_id)
        return customer
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/login",
    response_model=CustomerResponse,
    summary="Authenticate customer or administrator",
)
def login(payload: CustomerLoginRequest, db: Session = Depends(get_db)):
    """Authenticate customer with email and password."""
    customer = CustomerService.authenticate(db, email=payload.email, password=payload.password)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return customer


@router.get(
    "/customers",
    response_model=List[CustomerResponse],
    summary="List customers for demo switcher",
)
def list_customers(db: Session = Depends(get_db)):
    """Return all customer profiles (convenient for testing and demo switching)."""
    return CustomerService.list_all(db)


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer profile",
)
def get_customer_profile(customer_id: str, db: Session = Depends(get_db)):
    customer = CustomerService.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return customer
