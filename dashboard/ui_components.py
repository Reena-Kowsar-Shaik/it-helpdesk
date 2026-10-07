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
    /* Visual Progress Stepper */
    .stepper-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 14px 0 16px 0;
        padding: 10px 14px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
    }
    .stepper-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        flex: 1;
        text-align: center;
    }
    .stepper-step:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 13px;
        left: 55%;
        width: 90%;
        height: 3px;
        background: #E2E8F0;
        z-index: 1;
    }
    .stepper-step.completed:not(:last-child)::after {
        background: #10B981;
    }
    .stepper-step.active:not(:last-child)::after {
        background: #E2E8F0;
    }
    .stepper-icon {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        background: #FFFFFF;
        border: 2px solid #CBD5E1;
        color: #94A3B8;
        z-index: 2;
        margin-bottom: 4px;
        transition: all 0.2s ease;
    }
    .stepper-step.completed .stepper-icon {
        background: #10B981;
        border-color: #10B981;
        color: #FFFFFF;
    }
    .stepper-step.active .stepper-icon {
        background: #6366F1;
        border-color: #6366F1;
        color: #FFFFFF;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }
    .stepper-step.reopened .stepper-icon {
        background: #EF4444;
        border-color: #EF4444;
        color: #FFFFFF;
    }
    .stepper-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748B;
    }
    .stepper-step.completed .stepper-label {
        color: #059669;
    }
    .stepper-step.active .stepper-label {
        color: #4F46E5;
    }
    .stepper-step.reopened .stepper-label {
        color: #DC2626;
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


def get_sla_status_badge(deadline, is_resolved: bool = False, resolved_at = None) -> str:
    """Return an informative HTML badge for SLA countdown and breach state."""
    from datetime import datetime
    if not deadline:
        return '<span class="badge badge-closed">No SLA</span>'
    
    now = datetime.utcnow()
    if is_resolved and resolved_at:
        if resolved_at <= deadline:
            return '<span class="badge badge-resolved">🎯 Met SLA</span>'
        else:
            diff_hrs = round((resolved_at - deadline).total_seconds() / 3600.0, 1)
            return f'<span class="badge badge-reopened">⚠️ Resolved Late (+{diff_hrs}h)</span>'
    
    if now > deadline:
        overdue_mins = int((now - deadline).total_seconds() / 60.0)
        if overdue_mins >= 60:
            return f'<span class="badge badge-critical">🚨 Breached (+{overdue_mins//60}h {overdue_mins%60}m)</span>'
        return f'<span class="badge badge-critical">🚨 Breached (+{overdue_mins}m)</span>'
    
    remaining_mins = int((deadline - now).total_seconds() / 60.0)
    if remaining_mins <= 60:
        return f'<span class="badge badge-high">⏳ At Risk ({remaining_mins}m left)</span>'
    elif remaining_mins <= 180:
        return f'<span class="badge badge-in-progress">⏳ {remaining_mins//60}h {remaining_mins%60}m left</span>'
    else:
        return f'<span class="badge badge-open">✅ {remaining_mins//60}h remaining</span>'


def render_ticket_progress_stepper(status: str) -> str:
    """Renders a responsive visual stage progression stepper."""
    steps = [
        ("OPEN", "1", "Submitted"),
        ("ASSIGNED", "2", "Assigned"),
        ("IN PROGRESS", "3", "Investigating"),
        ("RESOLVED", "4", "Resolved"),
        ("CLOSED", "5", "Closed")
    ]
    
    status_order = {
        "OPEN": 0,
        "ASSIGNED": 1,
        "IN PROGRESS": 2,
        "RESOLVED": 3,
        "CLOSED": 4,
        "REOPENED": 2
    }
    current_idx = status_order.get(status.upper(), 0)
    is_reopened = (status.upper() == "REOPENED")
    
    html = ['<div class="stepper-container">']
    for idx, (code, step_num, label) in enumerate(steps):
        if is_reopened and code == "IN PROGRESS":
            cls = "reopened"
            icon = "&#8635;"
            label = "Reopened"
        elif idx < current_idx:
            cls = "completed"
            icon = "&#10003;"
        elif idx == current_idx:
            cls = "active"
            icon = step_num
        else:
            cls = "pending"
            icon = step_num
            
        html.append(f'<div class="stepper-step {cls}"><div class="stepper-icon">{icon}</div><div class="stepper-label">{label}</div></div>')
    html.append('</div>')
    return "".join(html)


