"""Tests for the event-driven notification outbox and AWS API Gateway integration."""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import httpx
from backend.services.outbox_service import process_all_pending_outbox


def test_customer_registration_enqueues_welcome_notification(client: TestClient):
    """Verify new registration creates a user_registered outbox record."""
    reg_payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "securepassword123",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201

    # Check notification audit
    audit_res = client.get("/api/v1/notifications/audit")
    assert audit_res.status_code == 200
    events = audit_res.json()
    welcome_events = [e for e in events if e["event_type"] == "user_registered" and e["recipient"] == "jane.doe@example.com"]
    assert len(welcome_events) == 1
    assert "Welcome to CloudCart" in welcome_events[0]["subject"]


def test_order_creation_and_status_changes_enqueue_events(client: TestClient):
    """Verify checkout and status transitions enqueue order_placed, payment_confirmed, order_shipped."""
    customers = client.get("/api/v1/auth/customers").json()
    products = client.get("/api/v1/products").json()

    order = client.post(
        "/api/v1/orders",
        json={
            "customer_id": customers[0]["id"],
            "items": [{"product_id": products[0]["id"], "quantity": 1}],
            "shipping_address": "99 Market St, Boston, MA",
            "payment_method": "simulated_card",
        },
    ).json()

    # Move to payment_confirmed -> packed -> shipped
    client.patch(f"/api/v1/orders/{order['id']}/status", json={"to_status": "payment_confirmed"})
    client.patch(f"/api/v1/orders/{order['id']}/status", json={"to_status": "packed"})
    client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"to_status": "shipped", "tracking_number": "TRK-BOST-1234"},
    )

    # Inspect audit log for this order
    audit_res = client.get(f"/api/v1/notifications/audit?order_id={order['id']}")
    assert audit_res.status_code == 200
    events = audit_res.json()
    event_types = [e["event_type"] for e in events]

    assert "order_placed" in event_types
    assert "payment_confirmed" in event_types
    assert "order_packed" in event_types
    assert "order_shipped" in event_types


@pytest.mark.anyio
async def test_outbox_dispatcher_records_aws_202_accepted(client: TestClient):
    """Verify outbox processor updates status to ACCEPTED and saves notification_id upon AWS 202."""
    from backend.database import SessionLocal
    from backend.services.outbox_service import enqueue_outbox_event

    db = SessionLocal()
    evt = enqueue_outbox_event(
        db=db,
        recipient="test.accepted@example.com",
        event_type="order_placed",
        subject="Order Placed",
        body="Order Placed Body",
    )
    db.commit()
    evt_id = evt.id
    db.close()

    mock_response = httpx.Response(
        status_code=202,
        json={"notification_id": "aws-uuid-888999", "status": "QUEUED"},
        request=httpx.Request("POST", "https://mock-url"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        processed = await process_all_pending_outbox()
        assert processed > 0

        audit_res = client.get("/api/v1/notifications/audit")
        events = audit_res.json()
        matching = [e for e in events if e["id"] == evt_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "ACCEPTED"
        assert matching[0]["notification_id"] == "aws-uuid-888999"
        assert matching[0]["external_http_status"] == 202


@pytest.mark.anyio
async def test_outbox_dispatcher_handles_aws_400_rejected(client: TestClient):
    """Verify outbox processor marks REJECTED when upstream returns 400 Bad Request."""
    from backend.database import SessionLocal
    from backend.services.outbox_service import enqueue_outbox_event

    db = SessionLocal()
    evt = enqueue_outbox_event(
        db=db,
        recipient="bad.syntax@example.com",
        event_type="order_placed",
        subject="Bad Syntax",
        body="Bad Syntax Body",
    )
    db.commit()
    evt_id = evt.id
    db.close()

    mock_400 = httpx.Response(
        status_code=400,
        json={"message": "Invalid recipient syntax"},
        request=httpx.Request("POST", "https://mock-url"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_400):
        await process_all_pending_outbox()

        audit_res = client.get("/api/v1/notifications/audit")
        events = audit_res.json()
        matching = [e for e in events if e["id"] == evt_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "REJECTED"
        assert matching[0]["external_http_status"] == 400


@pytest.mark.anyio
async def test_outbox_dispatcher_handles_timeout_as_uncertain(client: TestClient):
    """Verify timeout is recorded as UNCERTAIN without falsely claiming success."""
    from backend.database import SessionLocal
    from backend.services.outbox_service import enqueue_outbox_event

    db = SessionLocal()
    evt = enqueue_outbox_event(
        db=db,
        recipient="timeout.user@example.com",
        event_type="order_placed",
        subject="Timeout Test",
        body="Timeout Test Body",
    )
    db.commit()
    evt_id = evt.id
    db.close()

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException("Read timed out"),
    ):
        await process_all_pending_outbox()

        audit_res = client.get("/api/v1/notifications/audit")
        events = audit_res.json()
        matching = [e for e in events if e["id"] == evt_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "UNCERTAIN"
        assert "timed out" in matching[0]["error_message"].lower()
