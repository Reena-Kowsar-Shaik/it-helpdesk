import streamlit as st

def render_status_badge(status: str) -> str:
    """Returns HTML for modern SaaS status badges."""
    configs = {
        "Open": ("#0284c7", "#e0f2fe", "#bae6fd", "🔵 Open"),
        "Assigned": ("#6366f1", "#eef2ff", "#c7d2fe", "🟣 Assigned"),
        "In Progress": ("#d97706", "#fef3c7", "#fde68a", "⚡ In Progress"),
        "Pending Customer": ("#475569", "#f1f5f9", "#e2e8f0", "⏳ Pending"),
        "Resolved": ("#059669", "#ecfdf5", "#a7f3d0", "✅ Resolved"),
        "Closed": ("#334155", "#f1f5f9", "#e2e8f0", "🔒 Closed"),
        "Reopened": ("#dc2626", "#fef2f2", "#fecaca", "🔄 Reopened")
    }
    color, bg, border, label = configs.get(status, ("#475569", "#f1f5f9", "#e2e8f0", status))
    return f"""<span style="display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:9999px; font-size:0.75rem; font-weight:700; background:{bg}; color:{color}; border:1px solid {border}; letter-spacing:0.01em;">{label}</span>"""

def render_priority_badge(priority: str) -> str:
    """Returns HTML for modern priority badges."""
    configs = {
        "Critical": ("#dc2626", "#fef2f2", "#fecaca", "🔥 Critical"),
        "High": ("#ea580c", "#fff7ed", "#fed7aa", "⚠️ High"),
        "Medium": ("#0284c7", "#f0f9ff", "#bae6fd", "🔷 Medium"),
        "Low": ("#059669", "#f0fdf4", "#bbf7d0", "🟢 Low")
    }
    color, bg, border, label = configs.get(priority, ("#475569", "#f1f5f9", "#e2e8f0", priority))
    return f"""<span style="display:inline-flex; align-items:center; padding:3px 10px; border-radius:9999px; font-size:0.75rem; font-weight:700; background:{bg}; color:{color}; border:1px solid {border}; letter-spacing:0.01em;">{label}</span>"""

def render_sla_chip(sla_info: dict) -> str:
    """Renders SLA status chip."""
    label = sla_info.get("label", "N/A")
    is_breached = sla_info.get("is_breached", False)
    if is_breached:
        color = "#dc2626"
        bg = "#fef2f2"
        border = "#fecaca"
        icon = "🚨"
    else:
        color = "#0284c7"
        bg = "#f0f9ff"
        border = "#bae6fd"
        icon = "⏱️"
    return f"""<span style="display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:6px; font-size:0.75rem; font-weight:700; background:{bg}; color:{color}; border:1px solid {border}; font-family:'JetBrains Mono', monospace;">{icon} {label}</span>"""

def render_metric_card(title: str, value: str, subtitle: str = "", delta: str = "", delta_color: str = "#059669", icon: str = "📊", bg_badge: str = "#eff6ff"):
    """Renders executive KPI card."""
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-header">
            <span class="stat-label">{title}</span>
            <div class="stat-icon-badge" style="background:{bg_badge};">{icon}</div>
        </div>
        <div class="stat-value">{value}</div>
        <div class="stat-footer">
            <span>{subtitle}</span>
            <span style="color:{delta_color}; font-weight:700; font-family:'JetBrains Mono', monospace;">{delta}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
