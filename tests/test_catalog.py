"""Tests for product catalog browsing, filtering, and administration."""
from fastapi.testclient import TestClient


def test_list_products_returns_seeded_catalog(client: TestClient):
    """Verify customer can browse catalog and get seeded products."""
    res = client.get("/api/v1/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 9
    first = products[0]
    assert "name" in first
    assert "price" in first
    assert "stock_quantity" in first
    assert "category" in first


def test_search_and_category_filtering(client: TestClient):
    """Verify keyword search and category filtering work correctly."""
    # Filter by category
    res = client.get("/api/v1/products?category=Audio")
    assert res.status_code == 200
    audio_items = res.json()
    assert len(audio_items) >= 2
    for item in audio_items:
        assert item["category"] == "Audio"

    # Search keyword
    search_res = client.get("/api/v1/products?search=Keyboard")
    assert search_res.status_code == 200
    items = search_res.json()
    assert len(items) >= 1
    assert "Keyboard" in items[0]["name"]


def test_admin_create_and_update_product(client: TestClient):
    """Verify administrator can add new products and adjust stock."""
    new_product_payload = {
        "name": "CloudCart Wireless Fast Charger 15W",
        "description": "Qi-certified wireless charging pad with LED indicator and temperature control.",
        "category": "Accessories",
        "price": 29.99,
        "stock_quantity": 40,
        "image_url": "https://example.com/charger.jpg",
        "is_active": True,
    }
    create_res = client.post("/api/v1/products", json=new_product_payload)
    assert create_res.status_code == 201
    created = create_res.json()
    pid = created["id"]
    assert created["name"] == "CloudCart Wireless Fast Charger 15W"
    assert created["stock_quantity"] == 40

    # Admin updates stock to 55
    update_res = client.put(f"/api/v1/products/{pid}", json={"stock_quantity": 55, "price": 27.99})
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["stock_quantity"] == 55
    assert updated["price"] == 27.99
