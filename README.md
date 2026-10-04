# 🎫 IT Helpdesk & Ticket Management System

An Enterprise Ticket Management & SQL-Driven Support Intelligence Platform built with **Python OOP, MySQL, SQLAlchemy, Streamlit, and Plotly**.

---

## 👥 4-Member Project Division & Status

| Member | Focus Area | Status | Key Deliverables |
| :--- | :--- | :---: | :--- |
| **Member 1** | **Database Architect, Auth & Core OOP** | ✅ **Implemented** | `schema.sql`, `seed_data.sql`, `views.sql`, `core/models.py`, `core/repositories.py`, `core/auth.py`, `core/logger.py` |
| **Member 2** | **Ticket Operations & SLA Engine** | ✅ **Implemented** | `tickets/ticket_manager.py`, `tickets/ticket_assignment.py`, `tickets/ticket_history.py`, `tickets/sla_manager.py`, `tickets/ticket_filters.py` |
| **Member 3** | **Advanced SQL Analytics & BI** | ✅ **Implemented** | Complex queries, SQL views, procedures, ranking & SLA breach intelligence |
| **Member 4** | **Streamlit UI/UX & Dashboards** | ✅ **Implemented** | `app.py`, `dashboard/ui_components.py`, `dashboard/charts.py`, Employee / Agent / Executive Dashboards |

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database (Optional)
The system works out of the box with **MySQL** or automatically falls back to **local SQLite** (`it_helpdesk.db`). To connect to your MySQL instance:
1. Edit `config.py` or create a `.env` file (see `.env.example`):
   ```env
   DB_TYPE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=it_helpdesk_db
   ```
2. Run the seed script:
   ```bash
   python seed_db.py
   ```

### 3. Launch Streamlit Application
```bash
streamlit run app.py
```

---

## 🔐 Demo Credentials

| Role | Username | Password | Features Accessible |
| :--- | :--- | :--- | :--- |
| **👑 Admin** | `admin` | `admin123` | Executive KPI analytics, Plotly graphs, Agent leaderboard, SLA breaches, CSV exports |
| **👥 Team Lead** | `lead_vikram` | `lead123` | Operational queue, team assignment, agent workload metrics |
| **🎧 Support Agent** | `ravi_agent` | `agent123` | Active queue, ticket resolution form with root cause, public/internal notes |
| **👤 Employee** | `john_doe` | `employee123` | Raise tickets, track progress, add comments, reopen resolved tickets |

---

## 🗄️ Database Architecture (`sql/`)

- **`sql/schema.sql`**: 11 normalized tables with full referential integrity:
  - `departments`
  - `users`
  - `employees`
  - `support_teams`
  - `support_agents`
  - `categories`
  - `sla_rules`
  - `tickets`
  - `ticket_history`
  - `comments`
  - `ticket_resolutions`
- **`sql/views.sql`**: High-performance analytical views for SLA tracking, department load, and agent scorecards.
- **`sql/procedures.sql`**: Stored procedures for business intelligence reports.
- **`sql/triggers.sql`**: Automated audit history trail recording.

---

## 📂 Project Structure

```text
it_helpdesk_system/
│
├── .streamlit/
│   └── config.toml             # Dark theme styling config
│
├── app.py                      # Main Streamlit router & Auth portal
├── config.py                   # Environment & Database configuration
├── seed_db.py                  # Schema generation & seed runner
├── requirements.txt            # Python dependencies
│
├── core/                       # 👤 Member 1 Deliverables
│   ├── database.py             # SQLAlchemy Engine, Session Pool & Fallback
│   ├── models.py               # OOP Entities & Relationship Mappings
│   ├── repositories.py         # Data Access Layer & CRUD Repositories
│   ├── auth.py                 # Bcrypt password security & Session RBAC
│   ├── exceptions.py           # Domain-specific custom exceptions
│   └── logger.py               # Structured audit logging (logs/app.log)
│
├── tickets/                    # 👤 Member 2 Deliverables
│   ├── ticket_manager.py       # Core Ticket CRUD, Lifecycle & Resolution
│   ├── ticket_assignment.py    # Manual & Smart Workload-Aware Auto Routing
│   ├── ticket_history.py       # Complete Audit Trail & Stage Durations
│   ├── sla_manager.py          # SLA Deadlines, Breach Checks & Compliance
│   ├── ticket_filters.py       # Multi-criteria Filter Service & DataFrame Export
│   └── __init__.py             # Module Exports
│
├── analytics/                  # 👤 Member 3 Deliverables
│   ├── sql_queries.py          # Advanced SQL queries, CTEs, Window functions
│   ├── agent_analysis.py       # Agent performance & leaderboard analytics
│   ├── department_analysis.py  # Department ticket volume & SLA analysis
│   ├── sla_analysis.py         # SLA compliance & breach metrics
│   ├── workload_analysis.py    # Agent workload capacity & distribution
│   ├── recurring_issues.py     # Recurring problem identification
│   └── reports.py              # Exportable BI reports
│
├── dashboard/                  # 👤 Member 4 Deliverables
│   ├── ui_components.py        # CSS design system, KPI cards & badges
│   ├── charts.py               # Plotly charts (donuts, bars, gauges)
│   ├── employee_dashboard.py   # Employee ticket creation & tracking
│   ├── agent_dashboard.py      # Support queue, status transitions, resolutions
│   └── admin_dashboard.py      # Executive BI, SLA monitor & CSV exports
│
├── sql/                        # SQL Core
│   ├── schema.sql              # DDL Table Schemas & Constraints
│   ├── seed_data.sql           # Realistic Mock Data & Accounts
│   ├── views.sql               # Analytical SQL Views
│   ├── procedures.sql          # Stored Procedures
│   └── triggers.sql            # Audit History Triggers
│
└── logs/
    └── app.log                 # Security & Operational audit logs
```
