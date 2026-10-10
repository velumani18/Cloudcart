"""Seed initial realistic products and deterministic demo customers."""
from sqlalchemy.orm import Session
from backend.models import Customer, Product
from backend.repositories.customer_repository import hash_password


DEMO_CUSTOMERS = [
    {
        "name": "Alex Carter",
        "email": "alex.carter@example.com",
        "password": "password123",
        "is_admin": False,
    },
    {
        "name": "Sarah Lin",
        "email": "sarah.lin@example.com",
        "password": "password123",
        "is_admin": False,
    },
    {
        "name": "David Kim",
        "email": "david.kim@example.com",
        "password": "password123",
        "is_admin": False,
    },
    {
        "name": "CloudCart Admin",
        "email": "admin@cloudcart.example.com",
        "password": "adminpassword",
        "is_admin": True,
    },
]

DEMO_PRODUCTS = [
    {
        "name": "CloudPod Pro Wireless Earbuds",
        "description": "Active noise cancellation, spatial audio with dynamic head tracking, and 30-hour battery life.",
        "category": "Audio",
        "price": 129.99,
        "stock_quantity": 35,
        "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "Aura Studio ANC Headphones",
        "description": "Custom 40mm beryllium drivers delivering studio-grade hi-fi audio and ultra-plush memory foam pads.",
        "category": "Audio",
        "price": 249.99,
        "stock_quantity": 20,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "Nebula 27\" 4K IPS HDR Monitor",
        "description": "Ultra-sharp 3840x2160 resolution, 99% DCI-P3 color gamut, and 90W USB-C single cable power delivery.",
        "category": "Electronics",
        "price": 389.00,
        "stock_quantity": 15,
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "PulseFit Active Smartwatch",
        "description": "Continuous SpO2, heart rate, ECG tracking, 5ATM water resistance, and crisp AMOLED always-on display.",
        "category": "Wearables",
        "price": 89.50,
        "stock_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "Titanium RGB Mechanical Keyboard",
        "description": "Hot-swappable tactile switches, aircraft-grade aluminum top plate, and sound-dampening silicone foam.",
        "category": "Accessories",
        "price": 119.00,
        "stock_quantity": 25,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "ErgoStand Aluminum Laptop Riser",
        "description": "Adjustable dual-pivot ergonomic stand designed to dissipate heat and optimize posture.",
        "category": "Home Office",
        "price": 45.00,
        "stock_quantity": 40,
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "HyperSpeed 12-in-1 Thunderbolt 4 Dock",
        "description": "Dual 4K@60Hz display support, 2.5G Ethernet, SD Express 7.0 reader, and 100W laptop fast charging.",
        "category": "Electronics",
        "price": 159.00,
        "stock_quantity": 18,
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "Precision Silent Ergonomic Mouse",
        "description": "4000 DPI laser tracking on any surface, multi-device Bluetooth switching, and quiet acoustic switches.",
        "category": "Accessories",
        "price": 59.99,
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=60",
    },
    {
        "name": "Lumina Smart Desk Ambient Light Bar",
        "description": "Asymmetric optical design illuminating only your desk with zero screen glare and auto-dimming sensor.",
        "category": "Home Office",
        "price": 69.00,
        "stock_quantity": 22,
        "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500&auto=format&fit=crop&q=60",
    },
]


def seed_database(db: Session) -> None:
    """Populate database with demo customers and products if empty."""
    # 1. Seed customers
    if db.query(Customer).count() == 0:
        for c_data in DEMO_CUSTOMERS:
            cust = Customer(
                name=c_data["name"],
                email=c_data["email"].lower(),
                password_hash=hash_password(c_data["password"]),
                is_admin=c_data["is_admin"],
            )
            db.add(cust)
        db.commit()

    # 2. Seed products
    if db.query(Product).count() == 0:
        for p_data in DEMO_PRODUCTS:
            prod = Product(
                name=p_data["name"],
                description=p_data["description"],
                category=p_data["category"],
                price=p_data["price"],
                stock_quantity=p_data["stock_quantity"],
                image_url=p_data["image_url"],
                is_active=True,
            )
            db.add(prod)
        db.commit()
