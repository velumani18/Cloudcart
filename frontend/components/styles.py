"""Shared styling tokens and CSS for CloudCart storefront."""
import streamlit as st


def inject_custom_styles():
    """Inject modern e-commerce SaaS CSS stylesheet."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            html, body, [class*="css"] {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                color: #0F172A;
            }

            /* Product Card */
            .product-card {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 16px;
                transition: transform 0.15s ease, box-shadow 0.15s ease;
                margin-bottom: 20px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 100%;
            }
            .product-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.06);
                border-color: #93C5FD;
            }

            /* Product Image placeholder */
            .product-img-box {
                width: 100%;
                height: 180px;
                background-color: #F8FAFC;
                border-radius: 8px;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 12px;
            }
            .product-img-box img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }

            /* Price and Stock */
            .product-price {
                font-size: 20px;
                font-weight: 700;
                color: #1E3A8A;
            }
            .stock-badge {
                font-size: 11px;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 9999px;
            }
            .in-stock {
                background: #DCFCE7;
                color: #15803D;
            }
            .low-stock {
                background: #FEF3C7;
                color: #B45309;
            }
            .out-of-stock {
                background: #FEE2E2;
                color: #B91C1C;
            }

            /* Cart summary card */
            .summary-box {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            }

            /* Primary button enhancement */
            .stButton>button {
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.15s ease;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_order_status_badge(status: str) -> str:
    """Return inline HTML badge for order lifecycle status."""
    s = (status or "").lower()
    badges = {
        "placed": ("#EFF6FF", "#1D4ED8", "Order Placed"),
        "payment_confirmed": ("#ECFDF5", "#047857", "Payment Confirmed"),
        "packed": ("#F5F3FF", "#6D28D9", "Order Packed"),
        "shipped": ("#FEF3C7", "#B45309", "In Transit (Shipped)"),
        "delivered": ("#DCFCE7", "#15803D", "Delivered"),
        "cancelled": ("#FEE2E2", "#B91C1C", "Cancelled"),
        "refund_processed": ("#F1F5F9", "#475569", "Refund Processed"),
    }
    bg, text, label = badges.get(s, ("#F1F5F9", "#475569", s.title()))
    return f"""<span style="background-color: {bg}; color: {text}; border-radius: 9999px; padding: 3px 12px; font-size: 12px; font-weight: 600; display: inline-block;">{label}</span>"""
