"""Interactive Plotly charts for CloudMail analytics."""
from typing import Dict, Any, List
import plotly.graph_objects as go
import streamlit as st


def render_status_distribution_chart(stats: Dict[str, Any]):
    """Render a clean donut chart displaying submission status distribution."""
    labels = ["Accepted for Processing", "Rejected (Validation)", "Failed (Service)", "Uncertain (Timeout)"]
    values = [
        stats.get("total_accepted", 0),
        stats.get("total_rejected", 0),
        stats.get("total_failed", 0),
        stats.get("total_uncertain", 0),
    ]

    total = sum(values)
    if total == 0:
        st.info("No notification submissions recorded yet. Launch your first campaign to see the distribution.")
        return

    colors = ["#16A34A", "#F59E0B", "#EF4444", "#8B5CF6"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                textinfo="percent+value",
                hoverinfo="label+value+percent",
                sort=False,
            )
        ]
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(t=20, b=30, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=280,
        font=dict(family="sans-serif", size=12, color="#334155"),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_campaign_activity_chart(campaigns: List[Dict[str, Any]]):
    """Render a bar chart of recent campaign recipient volumes."""
    if not campaigns:
        return

    # Take up to last 7 campaigns
    reversed_camps = list(reversed(campaigns[:7]))
    names = [c.get("campaign_name", "Untitled")[:18] for c in reversed_camps]
    accepted = [c.get("accepted_count", 0) for c in reversed_camps]
    rejected_failed = [
        c.get("rejected_count", 0) + c.get("failed_count", 0) + c.get("uncertain_count", 0)
        for c in reversed_camps
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                name="Accepted",
                x=names,
                y=accepted,
                marker_color="#2563EB",
            ),
            go.Bar(
                name="Rejected / Failed",
                x=names,
                y=rejected_failed,
                marker_color="#94A3B8",
            ),
        ]
    )

    fig.update_layout(
        barmode="stack",
        margin=dict(t=20, b=20, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=260,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        yaxis=dict(gridcolor="#F1F5F9", title="Recipients"),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        font=dict(family="sans-serif", size=11, color="#475569"),
    )

    st.plotly_chart(fig, use_container_width=True)
