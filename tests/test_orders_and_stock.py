"""Tests for shopping cart checkout, transactional stock decrements, and order creation."""
from fastapi.testclient import TestClient


def test_order_creation_decrements_stock(client: TestClient):
    """Verify order creation decrements stock and calculates accurate subtotal/total."""
    # 1. Fetch customers and products
    customers = client.get("/api/v1/auth/customers").json()
    customer = customers[0]

    products = client.get("/api/v1/products?category=Audio").json()
    prod = products[0]
    initial_stock = prod["stock_quantity"]

    # 2. Place order for 2 units
    payload = {
        "customer_id": customer["id"],
        "items": [{"product_id": prod["id"], "quantity": 2}],
        "shipping_address": "742 Evergreen Terrace, Springfield, OR 97477",
        "payment_method": "simulated_card",
    }
    res = client.post("/api/v1/orders", json=payload)
    assert res.status_code == 201
    order_data = res.json()

    assert order_data["order_number"].startswith("ORD-")
    assert order_data["customer_name"] == customer["name"]
    assert order_data["total_amount"] == round(prod["price"] * 2, 2)
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["quantity"] == 2

    # 3. Verify stock was decremented
    updated_prod = client.get(f"/api/v1/products/{prod['id']}").json()
    assert updated_prod["stock_quantity"] == initial_stock - 2


def test_insufficient_stock_rejected(client: TestClient):
    """Verify customer cannot purchase quantities exceeding available stock."""
    customers = client.get("/api/v1/auth/customers").json()
    customer = customers[0]

    products = client.get("/api/v1/products").json()
    prod = products[0]
    current_stock = prod["stock_quantity"]

    # Attempt to order stock + 10
    payload = {
        "customer_id": customer["id"],
        "items": [{"product_id": prod["id"], "quantity": current_stock + 10}],
        "shipping_address": "123 Main St, Anytown, CA",
        "payment_method": "simulated_card",
    }
    res = client.post("/api/v1/orders", json=payload)
    assert res.status_code == 400
    assert "Insufficient stock" in res.json()["detail"]
