# CloudCart — Event-Driven E-commerce with Cloud Email Automation

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.x-orange.svg)](https://www.sqlalchemy.org/)
[![Tests Passing](https://img.shields.io/badge/tests-14%20passed-brightgreen.svg)](#automated-testing)

**CloudCart** is an event-driven e-commerce platform built with Python, FastAPI, and Streamlit. Unlike manual email-sending tools, CloudCart automatically generates and dispatches customer email notifications through an external AWS API Gateway whenever business operations occur (e.g., customer registration, checkout, payment verification, packaging, shipment, delivery, cancellation, and refunds).

---

## Architecture Overview

```
Customer or Administrator
          │
          ▼
Streamlit E-commerce Interface (Port 8501)
          │  REST HTTP Requests
          ▼
FastAPI Application Backend (Port 8000)
    ├─ Customer Service (Auth, Registration, Demo profiles)
    ├─ Product Service (Catalog, Search, Category filter)
    ├─ Order Service (Transactional Checkout, Inventory Decrement)
    ├─ Lifecycle Service (Strict State Machine transitions)
    └─ Transactional Outbox & Notification Service
          │  Asynchronous HTTPX (Bounded Concurrency)
          ▼
Upstream AWS API Gateway
https://zjergdi6he.execute-api.ap-south-1.amazonaws.com/notifications
          │
          ▼
Cloud Notification Queue & Asynchronous Delivery Infrastructure
```

### Transactional Outbox Pattern
To prevent lost notifications or inconsistent state between the database and the external AWS gateway:
1. When a business event occurs (e.g. checkout or status advance), the order mutation and a `NotificationOutbox` record (`status=PENDING`) are committed inside the **same database transaction**.
2. An asynchronous worker immediately dispatches the notification to the AWS API Gateway.
3. The response is recorded in the outbox (`status=ACCEPTED`, `external_http_status=202`, and the AWS `notification_id`).
4. If an external network outage occurs, the outbox retains the unsent event for replay.

---

## Automated Business Events & Email Rules

The platform automatically maps business lifecycle events to plain-text templates matching the AWS gateway single-recipient contract:

| Event Identifier | Trigger Condition | Notification Subject | Dynamic Content |
| :--- | :--- | :--- | :--- |
| `user_registered` | New customer account registered | *Welcome to CloudCart!* | Customer name, welcome message, account info |
| `order_placed` | Customer completes checkout | *Your CloudCart order has been confirmed.* | Order number, items list, total, delivery address |
| `payment_confirmed` | Simulated payment verified | *Payment received for your order.* | Order number, amount paid, payment reference |
| `order_packed` | Warehouse marks order as packed | *Your order is packed.* | Order number, packaging confirmation |
| `order_shipped` | Courier pickup / carrier tracking | *Your order has been shipped.* | Order number, carrier tracking number |
| `order_delivered` | Package delivered to recipient | *Your order has been delivered.* | Order number, delivery confirmation |
| `order_cancelled` | Eligible order cancelled | *Your order has been cancelled.* | Order number, cancellation reason |
| `refund_processed` | Reversal / refund issued | *Your refund has been processed.* | Order number, refund amount |

---

## Order Status Lifecycle State Machine

Orders follow strict forward-moving lifecycle transitions:

```
[ placed ]
    │
    ▼
[ payment_confirmed ] ────► [ cancelled ] ────► [ refund_processed ]
    │                             ▲
    ▼                             │
[ packed ] ───────────────────────┤
    │                             │
    ▼                             │
[ shipped ] ──────────────────────┘
    │
    ▼
[ delivered ] ────────────► [ refund_processed ]
```

*Illegal state transitions (such as reverting a delivered order to placed) are rejected at the domain level with HTTP 400.*

---

## Project Structure

```
cloud_mail_automation/
├── backend/
│   ├── main.py                  # FastAPI app entry point, CORS & startup seed
│   ├── config.py                # Environment configuration & limits
│   ├── database.py              # SQLAlchemy 2.x engine & session factory
│   ├── models.py                # ORM models (Customer, Product, Order, Outbox)
│   ├── schemas.py               # Pydantic validation schemas
│   ├── seed.py                  # Demo catalog and customer seed dataset
│   ├── routers/
│   │   ├── health.py            # GET /health
│   │   ├── auth.py              # POST /register, /login, GET /customers
│   │   ├── products.py          # GET /products, POST /products (Admin)
│   │   ├── orders.py            # POST /orders (Checkout), PATCH /orders/{id}/status
│   │   ├── notifications.py     # GET /notifications/audit
│   │   └── admin.py             # GET /admin/stats
│   ├── services/
│   │   ├── product_service.py   # Catalog queries & inventory checks
│   │   ├── customer_service.py  # Customer registration & auth
│   │   ├── order_service.py     # Transactional checkout & lifecycle transitions
│   │   ├── notification_service.py # Upstream AWS API Gateway HTTPX client
│   │   ├── outbox_service.py    # Transactional outbox persistence & worker
│   │   └── email_templates.py   # Centralized templates for all 8 events
│   └── repositories/
│       ├── product_repository.py
│       ├── customer_repository.py
│       ├── order_repository.py
│       └── notification_repository.py
├── frontend/
│   ├── app.py                   # Storefront landing & featured products
│   ├── api_client.py            # Reusable HTTP client communicating with FastAPI
│   ├── pages/
│   │   ├── 1_🛍️_Store.py        # Product catalog, category filter & search
│   │   ├── 2_🛒_Shopping_Cart.py # Cart management & decimal-safe totals
│   │   ├── 3_💳_Checkout.py      # Checkout & simulated payment
│   │   ├── 4_📦_Track_Order.py   # Real-time visual timeline & notification audit
│   │   ├── 5_📜_Order_History.py # Customer-scoped order history
│   │   └── 6_⚙️_Admin_Portal.py  # Admin lifecycle manager, catalog & outbox logs
│   └── components/
│       ├── navbar.py            # Top branding, customer demo switcher & cart badge
│       ├── styles.py            # E-commerce SaaS styling tokens
│       └── order_timeline.py    # Visual lifecycle progress tracker
├── tests/
│   ├── conftest.py              # In-memory SQLite fixtures & TestClient
│   ├── test_health.py           # Health check endpoint test
│   ├── test_catalog.py          # Catalog browsing, filtering & admin stock tests
│   ├── test_orders_and_stock.py # Checkout & inventory decrement tests
│   ├── test_lifecycle_and_events.py # Lifecycle transitions & inventory restoration
│   └── test_outbox_notifications.py # Outbox persistence & AWS status mapping tests
├── .env.example
├── .env
├── requirements.txt
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.11 or higher.

### 2. Virtual Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Linux / macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```env
AWS_NOTIFICATION_URL=https://zjergdi6he.execute-api.ap-south-1.amazonaws.com/notifications
BACKEND_URL=http://127.0.0.1:8000
HOST=127.0.0.1
PORT=8000
REQUEST_TIMEOUT_SECONDS=15
OUTBOX_MAX_CONCURRENCY=5
DATABASE_URL=sqlite:///./cloudcart.db
```

---

## Running the Application

### 1. Start FastAPI Application Backend (Terminal 1)
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Endpoint: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Start Streamlit Storefront (Terminal 2)
```bash
python -m streamlit run frontend/app.py
```
Opens in your browser at [http://localhost:8501](http://localhost:8501).

---

## Automated Testing

Run the full automated test suite with mocked AWS requests:
```bash
python -m pytest -v
```

All 14 tests run in memory without triggering real external emails:
- Catalog browsing, category filtering, keyword search
- Admin product creation & inventory updating
- Checkout with transactional stock decrement
- Stock overselling prevention
- Order status lifecycle transitions and illegal state rejection
- Stock restoration upon order cancellation
- Customer registration triggering welcome notification
- Checkout triggering order confirmation and payment receipt
- Upstream AWS HTTP 202 (Accepted), 400 (Rejected), and timeout (Uncertain) handling
