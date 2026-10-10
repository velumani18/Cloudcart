"""Page 1: Product Catalog Browsing and Shopping."""
import streamlit as st
from frontend.components.styles import inject_custom_styles
from frontend.components.navbar import render_header
from frontend.api_client import CloudCartAPIClient

st.set_page_config(page_title="Store — CloudCart", page_icon="🛍️", layout="wide")
inject_custom_styles()
render_header()

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="font-size: 26px; font-weight: 700; color: #0F172A; margin: 0;">Explore Catalog</h1>
        <p style="font-size: 14px; color: #64748B; margin: 4px 0 0 0;">
            Premium electronics, studio audio, and workstation ergonomics.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

client = CloudCartAPIClient()
categories = client.get_categories()

# Filter and Search Row
f_col1, f_col2 = st.columns([3, 1])
with f_col1:
    search_keyword = st.text_input("🔍 Search Products", placeholder="Search by name, category, or features...")
with f_col2:
    selected_cat = st.selectbox("Category Filter", ["All"] + categories)

products = client.list_products(
    category=None if selected_cat == "All" else selected_cat,
    search=search_keyword.strip() if search_keyword else None,
)

if not products:
    st.info("No products found matching your search criteria.")
else:
    # 3-column responsive grid
    cols_per_row = 3
    for i in range(0, len(products), cols_per_row):
        row_products = products[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, prod in enumerate(row_products):
            with cols[idx]:
                stock = prod.get("stock_quantity", 0)
                if stock > 5:
                    stock_class = "in-stock"
                    stock_label = f"In Stock ({stock})"
                    is_available = True
                elif stock > 0:
                    stock_class = "low-stock"
                    stock_label = f"Low Stock ({stock})"
                    is_available = True
                else:
                    stock_class = "out-of-stock"
                    stock_label = "Out of Stock"
                    is_available = False

                img_url = prod.get("image_url") or "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"

                st.markdown(
                    f"""
                    <div class="product-card">
                        <div class="product-img-box">
                            <img src="{img_url}" alt="{prod['name']}" onerror="this.src='https://via.placeholder.com/300x200?text=Product';">
                        </div>
                        <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase;">
                            {prod['category']}
                        </div>
                        <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 4px 0 6px 0;">
                            {prod['name']}
                        </div>
                        <div style="font-size: 12px; color: #475569; line-height: 1.4; margin-bottom: 12px; height: 50px; overflow: hidden;">
                            {prod['description']}
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <span class="product-price">${prod['price']:.2f}</span>
                            <span class="stock-badge {stock_class}">{stock_label}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                btn_col1, btn_col2 = st.columns([1, 2])
                with btn_col1:
                    qty = st.number_input(
                        "Qty",
                        min_value=1,
                        max_value=max(1, stock),
                        value=1,
                        key=f"qty_{prod['id']}",
                        label_visibility="collapsed",
                        disabled=not is_available,
                    )
                with btn_col2:
                    if st.button(
                        "Add to Cart",
                        key=f"add_{prod['id']}",
                        disabled=not is_available,
                        use_container_width=True,
                        type="primary" if is_available else "secondary",
                    ):
                        cart = st.session_state.cart
                        pid = prod["id"]
                        if pid in cart:
                            cart[pid]["quantity"] += qty
                        else:
                            cart[pid] = {
                                "name": prod["name"],
                                "price": prod["price"],
                                "quantity": qty,
                                "image_url": prod.get("image_url"),
                            }
                        st.toast(f"Added {qty}x '{prod['name']}' to cart!", icon="🛒")
                        st.rerun()
