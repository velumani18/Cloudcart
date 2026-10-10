"""Top navigation bar, shopping cart state, and customer demo switcher."""
import streamlit as st
from frontend.api_client import CloudCartAPIClient


def init_session_state():
    """Initialize shopping cart and active customer in session state."""
    if "cart" not in st.session_state:
        st.session_state.cart = {}  # {product_id: {"name": ..., "price": ..., "quantity": ..., "image_url": ...}}

    if "current_customer" not in st.session_state:
        client = CloudCartAPIClient()
        customers = client.list_customers()
        # Default to first non-admin customer
        for c in customers:
            if not c.get("is_admin"):
                st.session_state.current_customer = c
                break
        if "current_customer" not in st.session_state and customers:
            st.session_state.current_customer = customers[0]


def render_header():
    """Render top brand navigation with customer switcher and cart count."""
    init_session_state()
    client = CloudCartAPIClient()
    customers = client.list_customers()

    cart_count = sum(item["quantity"] for item in st.session_state.cart.values())
    curr_cust = st.session_state.get("current_customer", {})
    curr_name = curr_cust.get("name", "Guest")
    curr_email = curr_cust.get("email", "")

    # Sidebar customer selection & info
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="background: linear-gradient(135deg, #2563EB, #1E40AF); width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 18px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);">
                    🛒
                </div>
                <div>
                    <h2 style="margin: 0; font-size: 20px; font-weight: 700; color: #0F172A; letter-spacing: -0.02em;">CloudCart</h2>
                    <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 500; text-transform: uppercase;">Event-Driven Store</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Active Customer Profile / Switcher
        st.markdown("##### 👤 Active Customer Profile")
        if customers:
            cust_options = {c["id"]: f"{c['name']} ({'Admin' if c.get('is_admin') else c['email']})" for c in customers}
            current_id = curr_cust.get("id")
            selected_id = st.selectbox(
                "Switch Customer (Demo Mode)",
                options=list(cust_options.keys()),
                index=list(cust_options.keys()).index(current_id) if current_id in cust_options else 0,
                format_func=lambda x: cust_options[x],
                help="Switch active user to experience personalized shopping and scoped order history.",
            )
            if selected_id != current_id:
                for c in customers:
                    if c["id"] == selected_id:
                        st.session_state.current_customer = c
                        st.rerun()

        st.caption(f"Logged in as: **{curr_name}** (`{curr_email}`)")

        st.markdown("---")

        # Gateway health pill
        health = client.check_health()
        if health["healthy"]:
            st.markdown(
                """
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px;">
                    <div style="font-size: 12px; font-weight: 600; color: #166534; display: flex; align-items: center; gap: 6px;">
                        <span style="height: 8px; width: 8px; background-color: #16A34A; border-radius: 50%; display: inline-block;"></span>
                        AWS Event Dispatcher Online
                    </div>
                    <div style="font-size: 11px; color: #15803D; margin-top: 2px;">Transactional Outbox Active</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px;">
                    <div style="font-size: 12px; font-weight: 600; color: #991B1B;">Backend Offline</div>
                    <div style="font-size: 11px; color: #B91C1C;">FastAPI server on port 8000 unreachable</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 11px; color: #64748B;">
                <div style="font-weight: 600; color: #334155; margin-bottom: 4px;">AUTOMATIC CLOUD EVENTS</div>
                <div>• User Registration &rarr; Welcome Email<br/>
                • Order Checkout &rarr; Order Placed & Payment Confirmation<br/>
                • Admin Status Update &rarr; Packed / Shipped / Delivered / Cancelled
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Top banner in main view
    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                <h2 style="margin: 0; font-size: 24px; font-weight: 700; color: #0F172A;">CloudCart Storefront</h2>
                <span style="background: #EFF6FF; color: #1D4ED8; font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 9999px;">
                    Shopping as {curr_name}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_c2:
        st.markdown(
            f"""
            <div style="text-align: right; margin-bottom: 10px;">
                <span style="background: #F1F5F9; border: 1px solid #E2E8F0; padding: 6px 14px; border-radius: 8px; font-size: 14px; font-weight: 600; color: #1E293B;">
                    🛒 Cart ({cart_count})
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
