"""CloudCart — Event-Driven E-commerce Platform.
Main Storefront Landing Application.
"""
import streamlit as st
from frontend.components.styles import inject_custom_styles
from frontend.components.navbar import render_header
from frontend.api_client import CloudCartAPIClient

st.set_page_config(
    page_title="CloudCart — Event-Driven Store",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_styles()
render_header()

# Hero Banner
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); border-radius: 16px; padding: 32px 36px; color: white; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="max-width: 640px;">
            <div style="background: rgba(255,255,255,0.15); display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                Event-Driven Cloud Notifications
            </div>
            <h1 style="margin: 0 0 10px 0; font-size: 32px; font-weight: 800; color: white; line-height: 1.2;">
                Smart E-commerce, Instant Cloud Updates.
            </h1>
            <p style="margin: 0; font-size: 15px; color: #DBEAFE; line-height: 1.5;">
                Every purchase, payment, packaging, and shipment event automatically generates and dispatches customer notifications to AWS Cloud Notification API in real time.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation Cards
st.subheader("Explore the Platform")
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    st.markdown(
        """
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #1E3A8A;">🛍️ Product Catalog</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 6px;">Browse audio, electronics, and gadgets with real-time stock checks.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Browse Catalog", key="btn_hero_catalog", use_container_width=True):
        st.switch_page("pages/1_🛍️_Store.py")

with nav_col2:
    st.markdown(
        """
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #1E3A8A;">🛒 Shopping Cart</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 6px;">Review items, adjust quantities, and inspect decimal-safe totals.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Cart", key="btn_hero_cart", use_container_width=True):
        st.switch_page("pages/2_🛒_Shopping_Cart.py")

with nav_col3:
    st.markdown(
        """
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #1E3A8A;">📦 Track Orders</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 6px;">Follow your orders across the live fulfillment timeline.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Live Order Tracker", key="btn_hero_tracker", use_container_width=True):
        st.switch_page("pages/4_📦_Track_Order.py")

with nav_col4:
    st.markdown(
        """
        <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #1E3A8A;">⚙️ Admin Portal</div>
                <div style="font-size: 12px; color: #64748B; margin-top: 6px;">Advance order statuses, edit stock, and audit cloud notifications.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Admin Portal", key="btn_hero_admin", use_container_width=True):
        st.switch_page("pages/6_⚙️_Admin_Portal.py")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# Featured Products Showcase
st.subheader("Featured Products")
client = CloudCartAPIClient()
products = client.list_products(limit=4)

if products:
    p_cols = st.columns(min(len(products), 4))
    for idx, prod in enumerate(products[:4]):
        with p_cols[idx]:
            st.markdown(
                f"""
                <div class="product-card">
                    <div class="product-img-box">
                        <img src="{prod.get('image_url') or 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500'}" alt="{prod['name']}" onerror="this.src='https://via.placeholder.com/300x200?text=Product';">
                    </div>
                    <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase;">
                        {prod['category']}
                    </div>
                    <div style="font-size: 15px; font-weight: 700; color: #0F172A; margin: 4px 0 6px 0;">
                        {prod['name']}
                    </div>
                    <div style="font-size: 12px; color: #475569; line-height: 1.4; margin-bottom: 12px; flex-grow: 1;">
                        {prod['description'][:85]}...
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span class="product-price">${prod['price']:.2f}</span>
                        <span class="stock-badge in-stock">In Stock ({prod['stock_quantity']})</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Add to Cart", key=f"quick_add_{prod['id']}", use_container_width=True):
                cart = st.session_state.cart
                pid = prod["id"]
                if pid in cart:
                    cart[pid]["quantity"] += 1
                else:
                    cart[pid] = {
                        "name": prod["name"],
                        "price": prod["price"],
                        "quantity": 1,
                        "image_url": prod.get("image_url"),
                    }
                st.toast(f"Added '{prod['name']}' to cart!", icon="🛒")
                st.rerun()

st.markdown("---")
st.info(
    "**Transactional Outbox Guarantee**: Order creation and lifecycle changes are committed transactionally with their corresponding notification events, "
    "preventing lost notifications even under external network outages.",
    icon="🛡️",
)
