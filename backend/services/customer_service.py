"""Customer management business service."""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from backend.models import Customer
from backend.repositories.customer_repository import CustomerRepository
from backend.services.email_templates import render_user_registered_template
from backend.services.outbox_service import enqueue_outbox_event


class CustomerService:
    """Business operations for customers."""

    @staticmethod
    def register_customer(
        db: Session,
        name: str,
        email: str,
        password: str,
        is_admin: bool = False,
    ) -> Tuple[Customer, str]:
        """
        Register a new customer and enqueue automatic welcome email in Outbox.
        Returns (customer, outbox_event_id).
        """
        existing = CustomerRepository.get_by_email(db, email)
        if existing:
            raise ValueError(f"An account with email '{email}' already exists.")

        customer = CustomerRepository.create_customer(
            db=db,
            name=name,
            email=email,
            password=password,
            is_admin=is_admin,
        )

        # Enqueue welcome email event in Outbox
        tmpl = render_user_registered_template(customer_name=customer.name, email=customer.email)
        outbox_event = enqueue_outbox_event(
            db=db,
            recipient=customer.email,
            event_type=tmpl["event_type"],
            subject=tmpl["subject"],
            body=tmpl["body"],
            customer_id=customer.id,
        )
        db.commit()

        return customer, outbox_event.id

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[Customer]:
        return CustomerRepository.verify_credentials(db, email, password)

    @staticmethod
    def get_customer(db: Session, customer_id: str) -> Optional[Customer]:
        return CustomerRepository.get_by_id(db, customer_id)

    @staticmethod
    def list_all(db: Session) -> List[Customer]:
        return CustomerRepository.list_customers(db)
