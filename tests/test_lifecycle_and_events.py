"""Tests for order status lifecycle state transitions and audit history."""
from fastapi.testclient import TestClient


def test_order_lifecycle_transitions(client: TestClient):
    """Test full valid lifecycle progression: payment_confirmed -> packed -> shipped -> delivered."""
    # 1. Create order
    customers = client.get("/api/v1/auth/customers").json()
    products = client.get("/api/v1/products").json()

    order_payload = {
        "customer_id": customers[0]["id"],
        "items": [{"product_id": products[1]["id"], "quantity": 1}],
        "shipping_address": "456 Tech Parkway, Seattle, WA",
        "payment_method": "simulated_card",
    }
    order = client.post("/api/v1/orders", json=order_payload).json()
    order_id = order["id"]

    # Order initial state is placed
    assert order["status"] == "placed"

    # Advance to PAYMENT_CONFIRMED
    res_pay = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"to_status": "payment_confirmed", "notes": "Card payment captured", "changed_by": "system:gateway"},
    )
    assert res_pay.status_code == 200
    assert res_pay.json()["status"] == "payment_confirmed"

    # Advance to PACKED
    res_packed = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"to_status": "packed", "notes": "Packed in box #B-42", "changed_by": "warehouse:dave"},
    )
    assert res_packed.status_code == 200
    assert res_packed.json()["status"] == "packed"

    # Advance to SHIPPED
    res_shipped = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={
            "to_status": "shipped",
            "notes": "Handed to FedEx Express",
            "tracking_number": "TRK-9876543210",
            "changed_by": "logistics:amy",
        },
    )
    assert res_shipped.status_code == 200
    assert res_shipped.json()["status"] == "shipped"
    assert res_shipped.json()["tracking_number"] == "TRK-9876543210"

    # Advance to DELIVERED
    res_delivered = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"to_status": "delivered", "notes": "Left on front porch", "changed_by": "carrier:fedex"},
    )
    assert res_delivered.status_code == 200
    assert res_delivered.json()["status"] == "delivered"

    # Verify status history timeline
    timeline = res_delivered.json()["status_history"]
    statuses = [h["to_status"] for h in timeline]
    assert "placed" in statuses
    assert "payment_confirmed" in statuses
    assert "packed" in statuses
    assert "shipped" in statuses
    assert "delivered" in statuses


def test_invalid_lifecycle_transition_rejected(client: TestClient):
    """Verify invalid state machine transitions are rejected with HTTP 400."""
    customers = client.get("/api/v1/auth/customers").json()
    products = client.get("/api/v1/products").json()

    order = client.post(
        "/api/v1/orders",
        json={
            "customer_id": customers[0]["id"],
            "items": [{"product_id": products[2]["id"], "quantity": 1}],
            "shipping_address": "100 Innovation Way, Austin, TX",
            "payment_method": "simulated_card",
        },
    ).json()

    # Move to payment_confirmed -> packed -> shipped -> delivered
    client.patch(f"/api/v1/orders/{order['id']}/status", json={"to_status": "payment_confirmed"})
    client.patch(f"/api/v1/orders/{order['id']}/status", json={"to_status": "packed"})
    client.patch(f"/api/v1/orders/{order['id']}/status", json={"to_status": "shipped"})
    client.patch(f"/api/v1/orders/{order['id']}/status", json={"to_status": "delivered"})

    # Attempt to revert from DELIVERED to PLACED (illegal violation)
    illegal_res = client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"to_status": "placed", "notes": "Reverting delivered order"},
    )
    assert illegal_res.status_code == 400
    assert "Invalid order status transition" in illegal_res.json()["detail"]


def test_cancellation_restores_inventory(client: TestClient):
    """Verify order cancellation returns items back to available inventory."""
    customers = client.get("/api/v1/auth/customers").json()
    products = client.get("/api/v1/products").json()
    prod = products[3]
    initial_stock = prod["stock_quantity"]

    order = client.post(
        "/api/v1/orders",
        json={
            "customer_id": customers[0]["id"],
            "items": [{"product_id": prod["id"], "quantity": 3}],
            "shipping_address": "888 Harbor Blvd, San Diego, CA",
            "payment_method": "simulated_card",
        },
    ).json()

    # Cancel order
    cancel_res = client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"to_status": "cancelled", "cancellation_reason": "Customer changed mind"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Inventory must be restored
    refreshed_prod = client.get(f"/api/v1/products/{prod['id']}").json()
    assert refreshed_prod["stock_quantity"] == initial_stock
