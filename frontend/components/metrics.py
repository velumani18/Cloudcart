"""Visual KPI metric cards and status badge components."""
from typing import Any
import streamlit as st


def render_metric_card(title: str, value: Any, subtitle: str = "", border_color: str = "#E2E8F0"):
    """Render a clean, modern SaaS KPI card with responsive typography."""
    st.markdown(
        f"""
        <div style="background: white; border: 1px solid {border_color}; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04); margin-bottom: 12px;">
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; margin-bottom: 6px;">
                {title}
            </div>
            <div style="font-size: 28px; font-weight: 700; color: #0F172A; line-height: 1.1; margin-bottom: 4px;">
                {value}
            </div>
            <div style="font-size: 11px; color: #94A3B8;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_status_badge_html(status: str) -> str:
    """Return inline HTML pill badge for submission and campaign statuses."""
    s = (status or "").upper()

    if s == "ACCEPTED":
        bg, text, border = "#DCFCE7", "#15803D", "#86EFAC"
        label = "Accepted for Processing"
    elif s == "REJECTED":
        bg, text, border = "#FEF3C7", "#B45309", "#FCD34D"
        label = "Rejected (Validation)"
    elif s == "FAILED":
        bg, text, border = "#FEE2E2", "#B91C1C", "#FCA5A5"
        label = "Failed (Upstream)"
    elif s == "UNCERTAIN":
        bg, text, border = "#EDE9FE", "#6D28D9", "#C4B5FD"
        label = "Uncertain (Timeout)"
    elif s == "COMPLETED":
        bg, text, border = "#DCFCE7", "#15803D", "#86EFAC"
        label = "Completed"
    elif s == "PROCESSING":
        bg, text, border = "#DBEAFE", "#1D4ED8", "#93C5FD"
        label = "Processing..."
    elif s == "PARTIALLY_FAILED":
        bg, text, border = "#FFEDD5", "#C2410C", "#FDBA74"
        label = "Partially Completed"
    else:
        bg, text, border = "#F1F5F9", "#475569", "#CBD5E1"
        label = s or "Pending"

    return f"""<span style="background-color: {bg}; color: {text}; border: 1px solid {border}; border-radius: 9999px; padding: 2px 10px; font-size: 11px; font-weight: 600; display: inline-block; white-space: nowrap;">{label}</span>"""
