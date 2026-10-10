"""Sidebar navigation and branding component for CloudMail."""
import streamlit as st
from frontend.api_client import APIClient


def render_sidebar():
    """Render the standard CloudMail sidebar with branding and system status."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 20px 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="background: linear-gradient(135deg, #2563EB, #1D4ED8); width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 18px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);">
                        CM
                    </div>
                    <div>
                        <h2 style="margin: 0; font-size: 20px; font-weight: 700; color: #0F172A; letter-spacing: -0.02em;">CloudMail</h2>
                        <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">Cloud Email Automation</p>
                    </div>
                </div>
                <p style="margin-top: 12px; font-size: 12px; color: #475569; line-height: 1.4;">
                    One platform to compose, submit, and track cloud-powered email notifications.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Quick system health check
        client = APIClient()
        health = client.check_health()

        if health["healthy"]:
            st.markdown(
                """
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px; padding: 10px 12px; margin-bottom: 15px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="height: 8px; width: 8px; background-color: #16A34A; border-radius: 50%; display: inline-block;"></span>
                        <span style="font-size: 12px; font-weight: 600; color: #166534;">Backend Connected</span>
                    </div>
                    <div style="font-size: 11px; color: #15803D; margin-top: 4px;">FastAPI Gateway Online</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 6px; padding: 10px 12px; margin-bottom: 15px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="height: 8px; width: 8px; background-color: #DC2626; border-radius: 50%; display: inline-block;"></span>
                        <span style="font-size: 12px; font-weight: 600; color: #991B1B;">Backend Unreachable</span>
                    </div>
                    <div style="font-size: 11px; color: #B91C1C; margin-top: 4px;">Check if FastAPI is running on port 8000</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 11px; color: #64748B;">
                <div style="font-weight: 600; color: #334155; margin-bottom: 6px;">ARCHITECTURE</div>
                <div>Streamlit UI &rarr; FastAPI Backend &rarr; AWS API Gateway &rarr; Notification Queue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #E2E8F0; font-size: 11px; color: #94A3B8; text-align: center;">
                CloudMail v1.0.0 &bull; Production Ready
            </div>
            """,
            unsafe_allow_html=True,
        )
