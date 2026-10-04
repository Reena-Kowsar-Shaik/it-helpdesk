"""Reusable UI Components and Design System for Streamlit Dashboards."""

import streamlit as st

def apply_custom_styles():
    """Inject custom modern CSS for typography, cards, badges, and layout aesthetics."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-title {
        font-size: 0.84rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 6px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-open { background-color: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-assigned { background-color: rgba(168, 85, 247, 0.2); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.3); }
    .badge-in-progress { background-color: rgba(234, 179, 8, 0.2); color: #FACC15; border: 1px solid rgba(234, 179, 8, 0.3); }
    .badge-resolved { background-color: rgba(34, 197, 94, 0.2); color: #4ADE80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-closed { background-color: rgba(100, 116, 139, 0.2); color: #94A3B8; border: 1px solid rgba(100, 116, 139, 0.3); }
    .badge-reopened { background-color: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }

    .badge-critical { background-color: rgba(225, 29, 72, 0.2); color: #FB7185; border: 1px solid rgba(225, 29, 72, 0.4); }
    .badge-high { background-color: rgba(249, 115, 22, 0.2); color: #FB923C; border: 1px solid rgba(249, 115, 22, 0.4); }
    .badge-medium { background-color: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-low { background-color: rgba(74, 222, 128, 0.2); color: #86EFAC; border: 1px solid rgba(74, 222, 128, 0.4); }

    /* Timeline and audit styles */
    .timeline-item {
        border-left: 2px solid #334155;
        padding-left: 16px;
        margin-left: 8px;
        margin-bottom: 14px;
        position: relative;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -6px;
        top: 2px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #6366F1;
    }
    .timeline-date {
        font-size: 0.75rem;
        color: #64748B;
    }
    .timeline-text {
        font-size: 0.88rem;
        color: #E2E8F0;
        margin-top: 2px;
    }

    /* Comment bubbles */
    .comment-bubble {
        background: #1E293B;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-left: 3px solid #6366F1;
    }
    .comment-bubble.internal {
        border-left-color: #F59E0B;
        background: rgba(245, 158, 11, 0.08);
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_kpi_card(title: str, value: str, subtext: str = "", icon: str = ""):
    """Render a styled KPI summary card."""
    icon_html = f"<span style='float:right; font-size:1.4rem;'>{icon}</span>" if icon else ""
    card_html = f"""
    <div class="metric-card">
        {icon_html}
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-sub">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def get_status_badge(status: str) -> str:
    """Return HTML badge for ticket status."""
    class_map = {
        "OPEN": "badge-open",
        "ASSIGNED": "badge-assigned",
        "IN PROGRESS": "badge-in-progress",
        "RESOLVED": "badge-resolved",
        "CLOSED": "badge-closed",
        "REOPENED": "badge-reopened"
    }
    css_class = class_map.get(status.upper(), "badge-open")
    return f'<span class="badge {css_class}">{status}</span>'


def get_priority_badge(priority: str) -> str:
    """Return HTML badge for ticket priority."""
    class_map = {
        "Critical": "badge-critical",
        "High": "badge-high",
        "Medium": "badge-medium",
        "Low": "badge-low"
    }
    css_class = class_map.get(priority, "badge-medium")
    return f'<span class="badge {css_class}">{priority}</span>'
