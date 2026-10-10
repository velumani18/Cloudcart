"""HTTP client communicating with the CloudCart FastAPI backend."""
import os
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


class CloudCartAPIClient:
    """Client for CloudCart FastAPI application backend."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or DEFAULT_BACKEND_URL).rstrip("/")
        self.timeout = 25.0

    def check_health(self) -> Dict[str, Any]:
        """Check backend reachability and health status."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5.0)
            if resp.status_code == 200:
                return {"healthy": True, "data": resp.json(), "error": None}
            return {"healthy": False, "data": None, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"healthy": False, "data": None, "error": str(exc)}

    # Customer & Auth
    def list_customers(self) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.base_url}/api/v1/auth/customers", timeout=self.timeout)
            return resp.json() if resp.status_code == 200 else []
        except Exception:
            return []

    def register_customer(self, name: str, email: str, password: str) -> Dict[str, Any]:
        payload = {"name": name, "email": email, "password": password}
        try:
            resp = requests.post(f"{self.base_url}/api/v1/auth/register", json=payload, timeout=self.timeout)
            if resp.status_code == 201:
                return {"success": True, "data": resp.json(), "error": None}
            return {"success": False, "data": None, "error": resp.json().get("detail", resp.text)}
        except Exception as exc:
            return {"success": False, "data": None, "error": str(exc)}

    def login_customer(self, email: str, password: str) -> Dict[str, Any]:
        payload = {"email": email, "password": password}
        try:
            resp = requests.post(f"{self.base_url}/api/v1/auth/login", json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json(), "error": None}
            return {"success": False, "data": None, "error": resp.json().get("detail", "Invalid credentials")}
        except Exception as exc:
            return {"success": False, "data": None, "error": str(exc)}

    # Products Catalog
    def list_products(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params = {"include_inactive": str(include_inactive).lower()}
        if category and category.lower() != "all":
            params["category"] = category
        if search:
            params["search"] = search
        try:
            resp = requests.get(f"{self.base_url}/api/v1/products", params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data[:limit] if limit is not None else data
            return []
        except Exception:
            return []

    def get_categories(self) -> List[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/v1/products/categories", timeout=self.timeout)
            return resp.json() if resp.status_code == 200 else []
        except Exception:
            return []

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.base_url}/api/v1/products/{product_id}", timeout=self.timeout)
            return resp.json() if resp.status_code == 200 else None
        except Exception:
            return None

    def create_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = requests.post(f"{self.base_url}/api/v1/products", json=data, timeout=self.timeout)
            if resp.status_code == 201:
                return {"success": True, "data": resp.json(), "error": None}
            return {"success": False, "data": None, "error": resp.json().get("detail", resp.text)}
        except Exception as exc:
            return {"success": False, "data": None, "error": str(exc)}

    def update_product(self, product_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = requests.put(f"{self.base_url}/api/v1/products/{product_id}", json=data, timeout=self.timeout)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json(), "error": None}
            return {"success": False, "data": None, "error": resp.json().get("detail", resp.text)}
        except Exception as exc:
            return {"success": False, "data": None, "error": str(exc)}

    # Orders & Checkout
    def create_order(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        shipping_address: str,
        payment_method: str = "simulated_card",
    ) -> Dict[str, Any]:
        payload = {
            "customer_id": customer_id,
            "items": items,
            "shipping_address": shipping_address,
            "payment_method": payment_method,
        }
        try:
            resp = requests.post(f"{self.base_url}/api/v1/orders", json=payload, timeout=self.timeout)
            if resp.status_code == 201:
                return {"success": True, "data": resp.json(), "error": None}
            return {"success": False, "data": None, "error": resp.json().get("detail", resp.text)}
        except Exception as exc:
            return {"success": False, "data": None, "error": str(exc)}

    def list_orders(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        if customer_id:
            params["customer_id"] = customer_id
        if status and status.lower() != "all":
            params["status"] = status
        try:
            resp = requests.get(f"{self.base_url}/api/v1/orders", params=params, timeout=self.timeout)
            return resp.json() if resp.status_code == 200 else []
        except Exception:
            return []

    def get_order(self, order_id_or_number: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.base_url}/api/v1/orders/{order_id_or_number}", timeout=self.timeout)
            return resp.json() if resp.status_code == 200 else None
        except Exception:
            return None

    def update_order_status(
        self,
        order_id: str,
        to_status: str,
        notes: Optional[str] = None,
        tracking_number: Optional[str] = None,
        cancellation_reason: Optional[str] = None,
        changed_by: str = "admin",
    ) -> Dict[str, Any]:
        payload = {
            "to_status": to_status,
            "notes": notes,
            "tracking_number": tracking_number,
            "cancellation_reason": cancellation_reason,
            "changed_by": changed_by,
        }
        try:
            resp = requests.patch(f"{self.base_url}/api/v1/orders/{order_id}/status", json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json(), "error": None}
            return {"success": False, "data": None, "error": resp.json().get("detail", resp.text)}
        except Exception as exc:
            return {"success": False, "data": None, "error": str(exc)}

    # Notifications Outbox Audit
    def list_notifications(
        self,
        order_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        if order_id:
            params["order_id"] = order_id
        if customer_id:
            params["customer_id"] = customer_id
        if status and status.upper() != "ALL":
            params["status"] = status
        try:
            resp = requests.get(f"{self.base_url}/api/v1/notifications/audit", params=params, timeout=self.timeout)
            return resp.json() if resp.status_code == 200 else []
        except Exception:
            return []

    # Admin Stats
    def get_admin_stats(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.base_url}/api/v1/admin/stats", timeout=self.timeout)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}
