"""Customer account repository layer."""
import hashlib
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models import Customer


def hash_password(password: str) -> str:
    """Deterministic salted SHA-256 hash for secure storage."""
    salt = "cloudcart_secure_salt_2026"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class CustomerRepository:
    """Data access methods for Customers."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.email == email.strip().lower()).first()

    @staticmethod
    def get_by_id(db: Session, customer_id: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def create_customer(
        db: Session,
        name: str,
        email: str,
        password: str,
        is_admin: bool = False,
    ) -> Customer:
        customer = Customer(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            is_admin=is_admin,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def verify_credentials(db: Session, email: str, password: str) -> Optional[Customer]:
        customer = CustomerRepository.get_by_email(db, email)
        if not customer:
            return None
        if customer.password_hash == hash_password(password):
            return customer
        return None

    @staticmethod
    def list_customers(db: Session) -> List[Customer]:
        return db.query(Customer).order_by(Customer.created_at).all()
