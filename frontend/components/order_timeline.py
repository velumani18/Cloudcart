"""Visual Order Lifecycle Timeline Component."""
from typing import List, Dict, Any
import streamlit as st


def render_order_timeline(status: str, history: List[Dict[str, Any]]):
    """Render an intuitive visual step progress bar and audit timeline."""
    s = (status or "").lower()

    if s in ("cancelled", "refund_processed"):
        is_cancelled = True
        steps = [
            ("Order Placed", True),
            ("Payment Processed", True),
            ("Cancelled", True),
            ("Refund Processed", s == "refund_processed"),
        ]
    else:
        is_cancelled = False
        steps = [
            ("Placed", True),
            ("Payment Confirmed", s in ("payment_confirmed", "packed", "shipped", "delivered")),
            ("Packed", s in ("packed", "shipped", "delivered")),
            ("Shipped", s in ("shipped", "delivered")),
            ("Delivered", s == "delivered"),
        ]

    st.markdown(
        '<div style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; margin: 12px 0 10px 0;">'
        'Live Fulfillment Lifecycle'
        '</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(steps))
    for idx, (label, active) in enumerate(steps):
        with cols[idx]:
            if is_cancelled and label in ("Cancelled", "Refund Processed") and active:
                circle_color = "#DC2626" if label == "Cancelled" else "#475569"
            else:
                circle_color = "#2563EB" if active else "#94A3B8"

            icon = "✓" if active else str(idx + 1)
            bg_card = "#EFF6FF" if active else "#F8FAFC"
            border_card = "#BFDBFE" if active else "#E2E8F0"
            text_color = "#1E3A8A" if active else "#64748B"

            # Clean single-line HTML prevents Markdown from ever treating leading indentation as a code block
            st.markdown(
                f'<div style="background: {bg_card}; border: 1px solid {border_card}; border-radius: 10px; padding: 12px 6px; text-align: center;">'
                f'<div style="width: 28px; height: 28px; border-radius: 50%; background: {circle_color}; color: white; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; margin-bottom: 6px;">{icon}</div>'
                f'<div style="font-size: 12px; font-weight: 600; color: {text_color};">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Detailed history log expander
    if history:
        with st.expander("View Detailed Event Audit Log", expanded=False):
            for h in history:
                created_str = h.get("created_at", "")[:19].replace("T", " ")
                to_st = h.get("to_status", "").replace("_", " ").title()
                from_st = h.get("from_status", "")
                from_text = f" (transitioned from {from_st})" if from_st else ""
                notes = h.get("notes") or "Status updated."
                actor = h.get("changed_by", "system")

                st.markdown(
                    f'<div style="border-left: 3px solid #2563EB; padding-left: 12px; margin-bottom: 10px;">'
                    f'<div style="font-size: 13px; font-weight: 600; color: #1E293B;">{to_st}{from_text} &bull; <span style="font-size: 11px; font-weight: 400; color: #64748B;">{created_str} UTC</span></div>'
                    f'<div style="font-size: 12px; color: #475569; margin-top: 2px;">{notes} &mdash; <em>Recorded by: {actor}</em></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
