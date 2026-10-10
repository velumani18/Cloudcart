"""Page 5: Customer Order History (Strictly Scoped)."""
import streamlit as st
from frontend.components.styles import inject_custom_styles, get_order_status_badge
from frontend.components.navbar import render_header
from frontend.api_client import CloudCartAPIClient

st.set_page_config(page_title="My Orders — CloudCart", page_icon="📜", layout="wide")
inject_custom_styles()
render_header()

customer = st.session_state.get("current_customer", {})
cust_id = customer.get("id")
cust_name = customer.get("name", "Customer")

st.markdown(
    f"""
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #0F172A; margin: 0;">My Orders</h1>
        <p style="font-size: 14px; color: #64748B; margin: 4px 0 0 0;">
            Order history for <strong>{cust_name}</strong> ({customer.get('email')}).
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

client = CloudCartAPIClient()
orders = client.list_orders(customer_id=cust_id)

if not orders:
    st.markdown(
        """
        <div style="background: white; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 48px; text-align: center; margin: 24px 0;">
            <div style="font-size: 40px; margin-bottom: 12px;">📦</div>
            <h3 style="font-size: 18px; font-weight: 600; color: #0F172A; margin-bottom: 8px;">No Orders Placed Yet</h3>
            <p style="font-size: 13px; color: #64748B; max-width: 420px; margin: 0 auto 20px auto;">
                You haven't placed any orders with this customer account yet.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Start Shopping"):
        st.switch_page("pages/1_🛍️_Store.py")
else:
    for o in orders:
        created_str = o["created_at"][:19].replace("T", " ")
        items_count = sum(it["quantity"] for it in o.get("items", []))

        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 16px; font-weight: 700; color: #0F172A;">Order {o['order_number']}</span>
                        <span style="font-size: 12px; color: #64748B; margin-left: 8px;">{created_str} UTC</span>
                    </div>
                    <div>
                        {get_order_status_badge(o['status'])}
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #475569;">
                    <div>{items_count} item(s) &bull; Shipping to: {o['shipping_address'][:45]}...</div>
                    <div style="font-size: 16px; font-weight: 700; color: #1E3A8A;">${o['total_amount']:.2f}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Track Order {o['order_number']}", key=f"track_btn_{o['id']}"):
            st.session_state.tracking_search = o["order_number"]
            st.switch_page("pages/4_📦_Track_Order.py")
