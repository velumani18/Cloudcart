"""Page 2: Shopping Cart Review & Quantity Management."""
import streamlit as st
from frontend.components.styles import inject_custom_styles
from frontend.components.navbar import render_header

st.set_page_config(page_title="Shopping Cart — CloudCart", page_icon="🛒", layout="wide")
inject_custom_styles()
render_header()

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #0F172A; margin: 0;">Shopping Cart</h1>
        <p style="font-size: 14px; color: #64748B; margin: 4px 0 0 0;">
            Review your selected items and proceed to checkout.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

cart = st.session_state.cart

if not cart:
    st.markdown(
        """
        <div style="background: white; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 48px; text-align: center; margin: 24px 0;">
            <div style="font-size: 44px; margin-bottom: 12px;">🛒</div>
            <h3 style="font-size: 18px; font-weight: 600; color: #0F172A; margin-bottom: 8px;">Your Shopping Cart is Empty</h3>
            <p style="font-size: 13px; color: #64748B; max-width: 420px; margin: 0 auto 20px auto;">
                Explore our catalog of premium electronics, studio audio, and home office gear to add items to your cart.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Browse Products", type="primary"):
        st.switch_page("pages/1_🛍️_Store.py")
else:
    c_left, c_right = st.columns([3, 2], gap="large")

    subtotal = 0.0

    with c_left:
        st.subheader(f"Cart Items ({sum(it['quantity'] for it in cart.values())})")

        items_to_remove = []

        for pid, item in list(cart.items()):
            item_subtotal = round(item["price"] * item["quantity"], 2)
            subtotal = round(subtotal + item_subtotal, 2)

            st.markdown(
                f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <div style="width: 60px; height: 60px; border-radius: 8px; background: #F8FAFC; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                            <img src="{item.get('image_url') or 'https://via.placeholder.com/60'}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='https://via.placeholder.com/60?text=Item';">
                        </div>
                        <div>
                            <div style="font-size: 15px; font-weight: 700; color: #0F172A;">{item['name']}</div>
                            <div style="font-size: 13px; color: #64748B;">${item['price']:.2f} each</div>
                        </div>
                    </div>
                    <div style="font-size: 16px; font-weight: 700; color: #1E3A8A;">
                        ${item_subtotal:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Item controls
            q_col1, q_col2, q_col3 = st.columns([1, 1, 3])
            with q_col1:
                new_qty = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=99,
                    value=item["quantity"],
                    key=f"cart_qty_{pid}",
                    label_visibility="collapsed",
                )
                if new_qty != item["quantity"]:
                    cart[pid]["quantity"] = new_qty
                    st.rerun()
            with q_col2:
                if st.button("Remove", key=f"remove_{pid}"):
                    items_to_remove.append(pid)

        for pid in items_to_remove:
            del cart[pid]
            st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Clear Entire Cart"):
            st.session_state.cart = {}
            st.rerun()

    with c_right:
        st.subheader("Order Summary")
        tax = round(subtotal * 0.08, 2)
        total = round(subtotal + tax, 2)

        st.markdown(
            f"""
            <div class="summary-box">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: #475569;">
                    <span>Subtotal</span>
                    <span>${subtotal:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; color: #475569;">
                    <span>Estimated Shipping</span>
                    <span style="color: #16A34A; font-weight: 600;">FREE</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 16px; font-size: 14px; color: #475569;">
                    <span>Sales Tax (8%)</span>
                    <span>${tax:.2f}</span>
                </div>
                <div style="border-top: 1px solid #E2E8F0; padding-top: 16px; display: flex; justify-content: space-between; margin-bottom: 24px; font-size: 18px; font-weight: 700; color: #0F172A;">
                    <span>Total</span>
                    <span style="color: #1E3A8A;">${total:.2f}</span>
                </div>
                <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 12px; font-size: 12px; color: #1D4ED8; margin-bottom: 16px;">
                    ⚡ <strong>Automatic Cloud Notification</strong>: Upon checkout, CloudCart will immediately dispatch order confirmation and payment receipts to AWS Cloud Gateway.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Proceed to Checkout", type="primary", use_container_width=True):
            st.switch_page("pages/3_💳_Checkout.py")
