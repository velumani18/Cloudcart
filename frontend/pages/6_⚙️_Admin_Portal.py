"""Page 6: Administrator Operations, Lifecycle Management & Notification Audit."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from frontend.components.styles import inject_custom_styles, get_order_status_badge
from frontend.components.navbar import render_header
from frontend.api_client import CloudCartAPIClient
from backend.models import VALID_ORDER_TRANSITIONS

st.set_page_config(page_title="Admin Portal — CloudCart", page_icon="⚙️", layout="wide")
inject_custom_styles()
render_header()

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #0F172A; margin: 0;">CloudCart Admin Operations</h1>
        <p style="font-size: 14px; color: #64748B; margin: 4px 0 0 0;">
            Order lifecycle management, inventory control, and transactional cloud notification audit.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

client = CloudCartAPIClient()
stats = client.get_admin_stats()

tab_overview, tab_orders, tab_catalog, tab_audit = st.tabs([
    "📊 Overview & Analytics",
    "📦 Order Lifecycle Management",
    "🛍️ Catalog & Stock Control",
    "⚡ Cloud Notification Outbox",
])

# TAB 1: OVERVIEW & ANALYTICS
with tab_overview:
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Orders", stats.get("total_orders", 0))
    with kpi2:
        st.metric("Gross Revenue", f"${stats.get('total_revenue', 0.0):,.2f}")
    with kpi3:
        st.metric("Registered Customers", stats.get("total_customers", 0))
    with kpi4:
        st.metric("Active Products", stats.get("total_products", 0))

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.subheader("Order Status Distribution")
        order_counts = stats.get("order_status_counts", {})
        if order_counts:
            fig_orders = go.Figure(
                data=[
                    go.Pie(
                        labels=list(order_counts.keys()),
                        values=list(order_counts.values()),
                        hole=0.55,
                    )
                ]
            )
            fig_orders.update_layout(height=260, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_orders, use_container_width=True)
        else:
            st.caption("No orders recorded yet.")

    with c_chart2:
        st.subheader("Cloud Notification Outcomes")
        notif_counts = stats.get("notification_status_counts", {})
        if notif_counts:
            fig_notifs = go.Figure(
                data=[
                    go.Bar(
                        x=list(notif_counts.keys()),
                        y=list(notif_counts.values()),
                        marker_color=["#16A34A" if k == "ACCEPTED" else "#2563EB" for k in notif_counts.keys()],
                    )
                ]
            )
            fig_notifs.update_layout(height=260, margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Events")
            st.plotly_chart(fig_notifs, use_container_width=True)
        else:
            st.caption("No outbox notifications recorded yet.")

# TAB 2: ORDER LIFECYCLE MANAGEMENT
with tab_orders:
    st.subheader("Orders Lifecycle State Machine")

    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "placed", "payment_confirmed", "packed", "shipped", "delivered", "cancelled", "refund_processed"],
    )
    orders = client.list_orders(status=None if status_filter == "All" else status_filter)

    if not orders:
        st.info("No orders found matching this filter.")
    else:
        order_options = {o["id"]: f"{o['order_number']} — {o.get('customer_name')} (${o['total_amount']:.2f}) [{o['status'].title()}]" for o in orders}
        selected_order_id = st.selectbox(
            "Select Order to Advance Status",
            options=list(order_options.keys()),
            format_func=lambda x: order_options[x],
        )

        selected_order = next((o for o in orders if o["id"] == selected_order_id), None)
        if selected_order:
            curr_status = selected_order["status"]
            allowed_transitions = VALID_ORDER_TRANSITIONS.get(curr_status, [])

            st.markdown(
                f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin: 12px 0;">
                    <div><strong>Order Number:</strong> {selected_order['order_number']} &bull; <strong>Customer:</strong> {selected_order.get('customer_name')} ({selected_order.get('customer_email')})</div>
                    <div><strong>Current Lifecycle State:</strong> {get_order_status_badge(curr_status)}</div>
                    <div><strong>Allowed Transitions:</strong> {', '.join(allowed_transitions) if allowed_transitions else '<em>None (Terminal State)</em>'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not allowed_transitions:
                st.warning("This order is in a terminal state and cannot transition further.")
            else:
                up_col1, up_col2 = st.columns([1, 1])
                with up_col1:
                    target_status = st.selectbox("Target Status *", options=allowed_transitions)
                    notes = st.text_input("Operational Notes", placeholder="e.g. Dispatched with tracking info")
                with up_col2:
                    track_no = ""
                    cancel_reason = ""
                    if target_status == "shipped":
                        track_no = st.text_input("Tracking Number", placeholder="e.g. TRK-FDX-994821")
                    elif target_status == "cancelled":
                        cancel_reason = st.text_input("Cancellation Reason", placeholder="e.g. Item damaged / customer requested")

                if st.button("Execute Lifecycle Transition & Send Notification", type="primary"):
                    with st.spinner("Updating order and dispatching cloud event..."):
                        res = client.update_order_status(
                            order_id=selected_order_id,
                            to_status=target_status,
                            notes=notes.strip() if notes else None,
                            tracking_number=track_no.strip() if track_no else None,
                            cancellation_reason=cancel_reason.strip() if cancel_reason else None,
                            changed_by="admin_portal",
                        )
                        if res["success"]:
                            st.success(f"Order transitioned to **{target_status}**! Cloud notification queued to AWS.")
                            st.rerun()
                        else:
                            st.error(f"Transition error: {res['error']}")

# TAB 3: CATALOG & STOCK CONTROL
with tab_catalog:
    st.subheader("Product Inventory Management")
    all_prods = client.list_products(include_inactive=True)

    if all_prods:
        p_table = []
        for p in all_prods:
            p_table.append({
                "ID": p["id"][:8],
                "Name": p["name"],
                "Category": p["category"],
                "Price": f"${p['price']:.2f}",
                "Stock": p["stock_quantity"],
                "Status": "Active" if p["is_active"] else "Inactive",
            })
        st.dataframe(pd.DataFrame(p_table), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Adjust Existing Product Stock")
    if all_prods:
        p_choices = {p["id"]: f"{p['name']} (Current Stock: {p['stock_quantity']})" for p in all_prods}
        sel_p_id = st.selectbox("Choose Product", options=list(p_choices.keys()), format_func=lambda x: p_choices[x])
        sel_prod = next(p for p in all_prods if p["id"] == sel_p_id)

        st_c1, st_c2, st_c3 = st.columns([1, 1, 1])
        with st_c1:
            new_stock = st.number_input("Update Stock Quantity", value=sel_prod["stock_quantity"], min_value=0)
        with st_c2:
            new_price = st.number_input("Update Price ($)", value=float(sel_prod["price"]), min_value=0.01)
        with st_c3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Save Product Changes"):
                res = client.update_product(sel_p_id, {"stock_quantity": new_stock, "price": new_price})
                if res["success"]:
                    st.success("Product updated successfully!")
                    st.rerun()

# TAB 4: CLOUD NOTIFICATION AUDIT
with tab_audit:
    st.subheader("Transactional Outbox Audit Log")
    st.caption("Inspect all automatically generated business events and AWS Cloud Gateway responses.")

    all_notifs = client.list_notifications(limit=100)
    if not all_notifs:
        st.info("No outbox notifications found.")
    else:
        n_table = []
        for n in all_notifs:
            created_str = n["created_at"][:19].replace("T", " ")
            n_table.append({
                "Event Type": n["event_type"],
                "Recipient": n["recipient"],
                "Subject": n["subject"],
                "Status": n["status"],
                "HTTP Code": n.get("external_http_status") or "202",
                "AWS Notification ID": n.get("notification_id") or "None",
                "Timestamp (UTC)": created_str,
            })
        st.dataframe(pd.DataFrame(n_table), use_container_width=True, hide_index=True)
