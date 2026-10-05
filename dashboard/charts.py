"""Interactive Plotly Visualization Components."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Design Color Palette (Clean White/Light Theme)
LIGHT_LAYOUT = {
    "paper_bgcolor": "rgba(255,255,255,0)",
    "plot_bgcolor": "rgba(255,255,255,0)",
    "font": {"color": "#334155", "family": "Inter, sans-serif"},
    "margin": dict(l=20, r=20, t=40, b=20),
    "legend": dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
}

COLOR_MAP_STATUS = {
    "OPEN": "#3B82F6",
    "ASSIGNED": "#A855F7",
    "IN PROGRESS": "#EAB308",
    "RESOLVED": "#22C55E",
    "CLOSED": "#64748B",
    "REOPENED": "#EF4444"
}

COLOR_MAP_PRIORITY = {
    "Critical": "#E11D48",
    "High": "#F97316",
    "Medium": "#3B82F6",
    "Low": "#22C55E"
}

def create_status_donut(df: pd.DataFrame) -> go.Figure:
    """Create a sleek donut chart showing ticket status breakdown."""
    if df.empty or "status" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="No ticket data available", **LIGHT_LAYOUT)
        return fig

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    fig = px.pie(
        status_counts,
        names="Status",
        values="Count",
        hole=0.6,
        color="Status",
        color_discrete_map=COLOR_MAP_STATUS,
        title="Tickets by Status"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
    fig.update_layout(**LIGHT_LAYOUT)
    return fig


def create_priority_chart(df: pd.DataFrame) -> go.Figure:
    """Create a donut chart for ticket priorities."""
    if df.empty or "priority" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="No priority data available", **LIGHT_LAYOUT)
        return fig

    priority_counts = df["priority"].value_counts().reset_index()
    priority_counts.columns = ["Priority", "Count"]

    fig = px.pie(
        priority_counts,
        names="Priority",
        values="Count",
        hole=0.5,
        color="Priority",
        color_discrete_map=COLOR_MAP_PRIORITY,
        title="Tickets by Priority"
    )
    fig.update_traces(textposition='inside', textinfo='percent+value', marker=dict(line=dict(color='#FFFFFF', width=2)))
    fig.update_layout(**LIGHT_LAYOUT)
    return fig


def create_department_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart comparing ticket load across departments."""
    if df.empty or "department" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="No department data", **LIGHT_LAYOUT)
        return fig

    dept_counts = df.groupby(["department", "status"]).size().reset_index(name="Count")

    fig = px.bar(
        dept_counts,
        x="department",
        y="Count",
        color="status",
        color_discrete_map=COLOR_MAP_STATUS,
        barmode="stack",
        title="Department Volume by Status"
    )
    fig.update_layout(
        xaxis_title="Department",
        yaxis_title="Ticket Count",
        **LIGHT_LAYOUT
    )
    return fig


def create_sla_compliance_gauge(compliance_pct: float) -> go.Figure:
    """Gauge chart indicating SLA compliance percentage."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=compliance_pct,
        number={"suffix": "%", "font": {"size": 36, "color": "#0F172A"}},
        title={"text": "SLA Compliance Rate", "font": {"size": 16, "color": "#475569"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar": {"color": "#4F46E5"},
            "bgcolor": "#F1F5F9",
            "borderwidth": 1,
            "bordercolor": "#CBD5E1",
            "steps": [
                {"range": [0, 70], "color": "rgba(239, 68, 68, 0.2)"},
                {"range": [70, 90], "color": "rgba(234, 179, 8, 0.2)"},
                {"range": [90, 100], "color": "rgba(34, 197, 94, 0.2)"}
            ],
            "threshold": {
                "line": {"color": "#16A34A", "width": 3},
                "thickness": 0.75,
                "value": 95
            }
        }
    ))
    fig.update_layout(height=280, **LIGHT_LAYOUT)
    return fig


def create_agent_performance_bar(agent_data: list) -> go.Figure:
    """Grouped bar chart for agent resolved vs open tickets."""
    if not agent_data:
        fig = go.Figure()
        fig.update_layout(title="No agent performance data", **LIGHT_LAYOUT)
        return fig

    df = pd.DataFrame(agent_data)
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["agent_name"],
        y=df["resolved_tickets"],
        name="Resolved",
        marker_color="#22C55E"
    ))
    fig.add_trace(go.Bar(
        x=df["agent_name"],
        y=df["active_tickets"],
        name="Active / Open",
        marker_color="#EAB308"
    ))

    fig.update_layout(
        title="Agent Workload & Resolution Count",
        barmode="group",
        xaxis_title="Support Agent",
        yaxis_title="Total Tickets",
        **LIGHT_LAYOUT
    )
    return fig


def create_category_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of top recurring ticket categories."""
    if df.empty or "category" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="No category data", **LIGHT_LAYOUT)
        return fig

    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]

    fig = px.bar(
        cat_counts.sort_values(by="Count", ascending=True),
        x="Count",
        y="Category",
        orientation="h",
        color="Count",
        color_continuous_scale="Viridis",
        title="Recurring Issue Categories"
    )
    fig.update_layout(xaxis_title="Tickets", yaxis_title="", **LIGHT_LAYOUT)
    return fig
