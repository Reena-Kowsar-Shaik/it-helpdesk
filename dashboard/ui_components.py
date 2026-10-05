"""Reusable UI Components and Design System for Streamlit Dashboards."""

import streamlit as st

def apply_custom_styles():
    """Inject custom modern CSS for typography, cards, badges, and layout aesthetics in light mode."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Metric Card Styling (Clean Light Mode) */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.05), 0 1px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #6366F1;
        box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.12);
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 5px;
    }

    /* Badges (Crisp Light Theme) */
    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-open { background-color: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }
    .badge-assigned { background-color: #FAF5FF; color: #9333EA; border: 1px solid #E9D5FF; }
    .badge-in-progress { background-color: #FEFCE8; color: #CA8A04; border: 1px solid #FEF08A; }
    .badge-resolved { background-color: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0; }
    .badge-closed { background-color: #F8FAFC; color: #64748B; border: 1px solid #E2E8F0; }
    .badge-reopened { background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }

    .badge-critical { background-color: #FFF1F2; color: #E11D48; border: 1px solid #FFE4E6; }
    .badge-high { background-color: #FFF7ED; color: #EA580C; border: 1px solid #FFEDD5; }
    .badge-medium { background-color: #EFF6FF; color: #2563EB; border: 1px solid #DBEAFE; }
    .badge-low { background-color: #F0FDF4; color: #16A34A; border: 1px solid #DCFCE7; }

    /* Timeline and audit styles */
    .timeline-item {
        border-left: 2px solid #CBD5E1;
        padding-left: 14px;
        margin-left: 6px;
        margin-bottom: 12px;
        position: relative;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -5px;
        top: 3px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #6366F1;
    }
    .timeline-date {
        font-size: 0.74rem;
        color: #64748B;
    }
    .timeline-text {
        font-size: 0.86rem;
        color: #1E293B;
        margin-top: 2px;
    }

    /* Comment bubbles */
    .comment-bubble {
        background: #F8FAFC;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border: 1px solid #E2E8F0;
        border-left: 3px solid #6366F1;
        color: #1E293B;
    }
    .comment-bubble.internal {
        border-left-color: #F59E0B;
        background: #FFFBEB;
        border-color: #FEF3C7;
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
