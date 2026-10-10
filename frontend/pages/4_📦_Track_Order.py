"""Page 4: Live Order Tracking, Real-Time Timeline & Automated Notifications."""
import streamlit as st
from frontend.components.styles import inject_custom_styles, get_order_status_badge
from frontend.components.navbar import render_header
from frontend.components.order_timeline import render_order_timeline
from frontend.api_client import CloudCartAPIClient
from backend.models import VALID_ORDER_TRANSITIONS

st.set_page_config(page_title="Track Order — CloudCart", page_icon="📦", layout="wide")
inject_custom_styles()
render_header()

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #0F172A; margin: 0;">Live Order Tracking</h1>
        <p style="font-size: 14px; color: #64748B; margin: 4px 0 0 0;">
            Follow your order across the fulfillment pipeline and verify cloud notifications in real time.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

client = CloudCartAPIClient()
customer = st.session_state.get("current_customer", {})

# Search Input
default_search = st.session_state.get("tracking_search", "")
search_code = st.text_input("Enter Order Number or ID", value=default_search, placeholder="e.g. ORD-1001-382")

# Also provide customer's recent orders dropdown for quick selection
customer_orders = client.list_orders(customer_id=customer.get("id"))
if customer_orders and not search_code:
    options = {o["order_number"]: f"{o['order_number']} — ${o['total_amount']:.2f} ({o['status'].title()})" for o in customer_orders}
    selected_from_list = st.selectbox(
        "Or choose one of your recent orders:",
        options=["Select an order..."] + list(options.keys()),
        format_func=lambda x: options.get(x, x),
    )
    if selected_from_list != "Select an order...":
        search_code = selected_from_list

if not search_code.strip():
    st.info("Please enter an Order Number above or select one from your orders list.")
else:
    order = client.get_order(search_code.strip())
    if not order:
        st.error(f"Order '{search_code}' not found. Please double-check the order number.")
    else:
        # Header Info Card
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
                    <div>
                        <h2 style="margin: 0; font-size: 20px; font-weight: 700; color: #0F172A;">Order {order['order_number']}</h2>
                        <div style="font-size: 12px; color: #64748B;">Placed on {order['created_at'][:19].replace('T', ' ')} UTC</div>
                    </div>
                    <div>
                        {get_order_status_badge(order['status'])}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 13px; color: #334155;">
                    <div><strong>Recipient:</strong> {order.get('customer_name')} ({order.get('customer_email')})</div>
                    <div><strong>Total Amount:</strong> ${order['total_amount']:.2f}</div>
                    <div><strong>Tracking Number:</strong> {order.get('tracking_number') or 'Pending carrier handover'}</div>
                    <div><strong>Shipping Address:</strong> {order['shipping_address']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Visual Step Timeline (Fixed - renders cleanly without markdown code block)
        render_order_timeline(order["status"], order.get("status_history", []))

        # Quick Next-Step Fulfillment Simulation (No admin required!)
        curr_status = order["status"]
        allowed = VALID_ORDER_TRANSITIONS.get(curr_status, [])
        if allowed:
            next_step = allowed[0]  # Next natural progression (e.g., packed, shipped, delivered)
            step_labels = {
                "payment_confirmed": "Confirm Payment (Triggers payment_confirmed notification)",
                "packed": "Mark as Packed (Triggers order_packed notification)",
                "shipped": "Hand over to Courier (Triggers order_shipped notification)",
                "delivered": "Confirm Delivery (Triggers order_delivered notification)",
                "refund_processed": "Issue Refund (Triggers refund_processed notification)",
            }
            label_text = step_labels.get(next_step, f"Advance to {next_step.title()}")

            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px dashed #93C5FD; border-radius: 10px; padding: 14px 18px; margin: 16px 0;">
                    <div style="font-size: 13px; font-weight: 600; color: #1E3A8A; margin-bottom: 4px;">⚡ Instant Lifecycle Simulation</div>
                    <div style="font-size: 12px; color: #64748B;">Advance to the next fulfillment milestone to automatically dispatch its cloud email notification to AWS.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"🚀 Advance Order to '{next_step.title()}'", type="secondary"):
                with st.spinner(f"Advancing order to {next_step} and sending cloud notification..."):
                    trk = "TRK-EXP-99281" if next_step == "shipped" else None
                    res = client.update_order_status(
                        order_id=order["id"],
                        to_status=next_step,
                        notes=f"Auto-advanced to {next_step}.",
                        tracking_number=trk,
                        changed_by="quick_simulator",
                    )
                    if res["success"]:
                        st.toast(f"Order updated to '{next_step}'! Notification sent to AWS.", icon="✉️")
                        st.rerun()

        # Items List & Cloud Notification Audit
        col_items, col_notifs = st.columns([1, 1], gap="large")

        with col_items:
            st.subheader("Items in this Order")
            for item in order.get("items", []):
                st.markdown(
                    f"""
                    <div style="background: white; border: 1px solid #F1F5F9; border-radius: 8px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #0F172A;">{item['product_name']}</div>
                            <div style="font-size: 12px; color: #64748B;">Qty: {item['quantity']} &bull; ${item['unit_price']:.2f} each</div>
                        </div>
                        <div style="font-weight: 700; color: #1E3A8A;">
                            ${item['subtotal']:.2f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_notifs:
            st.subheader("Cloud Notifications Dispatched to AWS Gateway")
            notifications = client.list_notifications(order_id=order["id"])
            if not notifications:
                st.caption("No cloud notifications logged yet.")
            else:
                for notif in notifications:
                    n_status = notif.get("status", "PENDING")
                    badge_color = "#16A34A" if n_status == "ACCEPTED" else ("#DC2626" if n_status == "FAILED" else "#2563EB")
                    st.markdown(
                        f"""
                        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="font-weight: 700; font-size: 13px; color: #0F172A;">Event: <code>{notif['event_type']}</code></span>
                                <span style="color: {badge_color}; font-weight: 700; font-size: 11px;">{n_status} (HTTP {notif.get('external_http_status') or '202'})</span>
                            </div>
                            <div style="font-size: 12px; color: #475569;"><strong>Subject:</strong> {notif['subject']}</div>
                            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">AWS Notification ID: <code>{notif.get('notification_id') or 'Generated on AWS Queue'}</code></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
