"""Page 3: Order Checkout & Automated Cloud Notification Dispatch."""
import streamlit as st
from frontend.components.styles import inject_custom_styles
from frontend.components.navbar import render_header
from frontend.api_client import CloudCartAPIClient

st.set_page_config(page_title="Checkout — CloudCart", page_icon="💳", layout="wide")
inject_custom_styles()
render_header()

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #0F172A; margin: 0;">Order Checkout</h1>
        <p style="font-size: 14px; color: #64748B; margin: 4px 0 0 0;">
            Place your order. Email notifications are automatically dispatched to the cloud gateway upon checkout.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

cart = st.session_state.cart
customer = st.session_state.get("current_customer", {})
client = CloudCartAPIClient()

if not cart and "confirmed_order" not in st.session_state:
    st.info("Your cart is empty. Please select products from the store before checking out.")
    if st.button("Return to Store"):
        st.switch_page("pages/1_🛍️_Store.py")
elif "confirmed_order" in st.session_state:
    # Order Confirmation View
    order = st.session_state.confirmed_order
    order_id = order.get("id")

    # Fetch live notification status from backend
    notifs = client.list_notifications(order_id=order_id)

    st.markdown(
        f"""
        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 24px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 28px;">🎉</span>
                <div>
                    <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #166534;">Order Successfully Placed!</h2>
                    <div style="font-size: 14px; color: #15803D;">Order Number: <strong>{order.get('order_number')}</strong></div>
                </div>
            </div>
            <p style="font-size: 13px; color: #166534; line-height: 1.5; margin: 0 0 16px 0;">
                No manual admin verification required! An automated <code>order_placed</code> email notification has been immediately dispatched to the AWS Cloud Notification Gateway for <strong>{order.get('customer_email')}</strong>.
            </p>
            <div style="background: white; border: 1px solid #DCFCE7; border-radius: 8px; padding: 14px; font-size: 13px; color: #334155;">
                <strong>Total Amount:</strong> ${order.get('total_amount', 0):.2f} (Payment Method: {order.get('payment_method', 'simulated_card')})<br/>
                <strong>Delivery Address:</strong> {order.get('shipping_address')}<br/>
                <strong>Order Status:</strong> {order.get('status', 'placed').title()} &bull; Ready for Fulfillment
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display Immediate Cloud Notification Audit
    if notifs:
        st.subheader("Cloud Notification Dispatched to AWS Gateway")
        for n in notifs:
            n_status = n.get("status", "PENDING")
            badge_color = "#16A34A" if n_status == "ACCEPTED" else ("#DC2626" if n_status == "FAILED" else "#2563EB")
            http_code = n.get("external_http_status") or 202
            aws_id = n.get("notification_id") or "Generated on AWS Queue"

            st.markdown(
                f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; color: #0F172A; font-size: 14px;">Event: <code>{n.get('event_type')}</code></span>
                        <span style="background: #DCFCE7; color: {badge_color}; border: 1px solid #86EFAC; font-weight: 700; font-size: 11px; padding: 3px 10px; border-radius: 9999px;">
                            {n_status} (HTTP {http_code})
                        </span>
                    </div>
                    <div style="font-size: 13px; color: #334155; margin-bottom: 4px;">
                        <strong>Subject:</strong> {n.get('subject')}
                    </div>
                    <div style="font-size: 12px; color: #64748B;">
                        <strong>Recipient:</strong> <code>{n.get('recipient')}</code> &bull; <strong>AWS Notification ID:</strong> <code>{aws_id}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    btn_c1, btn_c2 = st.columns([1, 1])
    with btn_c1:
        if st.button("Track This Order Live", type="primary", use_container_width=True):
            st.session_state.tracking_search = order.get("order_number")
            st.switch_page("pages/4_📦_Track_Order.py")
    with btn_c2:
        if st.button("Continue Shopping", use_container_width=True):
            del st.session_state.confirmed_order
            st.switch_page("pages/1_🛍️_Store.py")
else:
    # Checkout Form
    subtotal = sum(round(it["price"] * it["quantity"], 2) for it in cart.values())
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + tax, 2)

    col_form, col_summary = st.columns([3, 2], gap="large")

    with col_form:
        st.subheader("1. Customer & Shipping Details")

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 16px; font-size: 13px;">
                <strong>Ordering As:</strong> {customer.get('name', 'Guest')}<br/>
                <strong>Notification Recipient:</strong> <code>{customer.get('email')}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

        shipping_addr = st.text_area(
            "Shipping Address *",
            value="452 Innovation Blvd, Suite 300, Seattle, WA 98101",
            help="Enter physical destination address.",
            height=90,
        )

        st.subheader("2. Payment Method")
        st.markdown(
            """
            <div style="background: white; border: 1px solid #93C5FD; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #1E3A8A; font-size: 14px;">Simulated Card Transaction</span>
                    <span style="background: #DBEAFE; color: #1D4ED8; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;">Sandbox Mode</span>
                </div>
                <div style="font-size: 12px; color: #64748B; line-height: 1.4;">
                    Demonstrates atomic order placement and automatic cloud email notification dispatches without real financial debit.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        card_number = st.text_input("Card Number", value="•••• •••• •••• 4242", disabled=True)

    with col_summary:
        st.subheader("Order Items")

        for it in cart.values():
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; color: #334155;">
                    <span>{it['name']} x{it['quantity']}</span>
                    <strong>${it['price'] * it['quantity']:.2f}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="summary-box" style="margin-top: 16px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; color: #64748B;">
                    <span>Subtotal</span>
                    <span>${subtotal:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; color: #64748B;">
                    <span>Sales Tax (8%)</span>
                    <span>${tax:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 18px; font-weight: 700; color: #0F172A; border-top: 1px solid #E2E8F0; padding-top: 10px; margin-bottom: 16px;">
                    <span>Total</span>
                    <span style="color: #1E3A8A;">${total:.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Confirm & Place Order", type="primary", use_container_width=True):
            if not shipping_addr.strip():
                st.error("Shipping address is required.")
            else:
                with st.spinner("Submitting order and dispatching email notifications to AWS Gateway..."):
                    items_payload = [{"product_id": pid, "quantity": it["quantity"]} for pid, it in cart.items()]

                    res = client.create_order(
                        customer_id=customer["id"],
                        items=items_payload,
                        shipping_address=shipping_addr.strip(),
                        payment_method="simulated_card",
                    )

                    if res["success"]:
                        st.session_state.cart = {}
                        st.session_state.confirmed_order = res["data"]
                        st.rerun()
                    else:
                        st.error(f"Checkout failed: {res['error']}")
