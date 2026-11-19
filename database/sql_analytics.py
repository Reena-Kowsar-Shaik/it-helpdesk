"""
SQL Analytics Masterclass & Business Intelligence Query Catalog.
Each query demonstrates key SQL concepts:
- Common Table Expressions (CTEs)
- Window Functions (RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD, Moving Averages)
- Aggregate Functions (COUNT, SUM, AVG, MIN, MAX)
- GROUP BY and HAVING clauses
- Multiple Relational JOINs (INNER, LEFT, SELF)
- Subqueries and Correlated Subqueries
- Conditional CASE expressions and Matrix Pivoting
- Date and Timestamp functions (DATEDIFF, strftime, julianday, TIMESTAMPDIFF)
- Views, Indexes, Constraints, and Transactions
"""

SQL_QUERIES_CATALOG = [
    {
        "id": "q1_agent_ranking_window",
        "title": "1. Support Agent Performance Leaderboard with Window Functions",
        "category": "Window Functions & CTEs",
        "concepts": ["Common Table Expressions (CTE)", "RANK() OVER()", "DENSE_RANK() OVER()", "LEFT JOIN", "CASE Expressions", "NULLIF", "ROUND"],
        "business_question": "How are support agents ranked overall and within their respective teams based on resolved tickets, resolution rate, and SLA compliance?",
        "sql": """WITH agent_stats AS (
    SELECT 
        a.agent_id,
        u.full_name AS agent_name,
        st.name AS team_name,
        a.tier,
        COUNT(t.ticket_id) AS total_assigned,
        SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS tickets_resolved,
        SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_tickets,
        SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_tickets,
        ROUND(AVG(CASE WHEN t.satisfaction_rating IS NOT NULL THEN t.satisfaction_rating END), 2) AS avg_csat
    FROM agents a
    JOIN users u ON a.user_id = u.user_id
    LEFT JOIN support_teams st ON a.team_id = st.team_id
    LEFT JOIN tickets t ON a.agent_id = t.assigned_agent_id
    GROUP BY a.agent_id, u.full_name, st.name, a.tier
)
SELECT 
    agent_id,
    agent_name,
    team_name,
    tier,
    total_assigned,
    tickets_resolved,
    active_tickets,
    breached_tickets,
    avg_csat,
    ROUND((tickets_resolved * 100.0) / NULLIF(total_assigned, 0), 1) AS resolution_rate_pct,
    ROUND(((tickets_resolved - breached_tickets) * 100.0) / NULLIF(tickets_resolved, 0), 1) AS sla_compliance_pct,
    RANK() OVER (ORDER BY tickets_resolved DESC, avg_csat DESC) AS company_wide_rank,
    DENSE_RANK() OVER (PARTITION BY team_name ORDER BY tickets_resolved DESC) AS rank_within_team
FROM agent_stats
ORDER BY company_wide_rank ASC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **CTE (`WITH agent_stats AS (...)`)**: Pre-computes per-agent aggregates from raw tables before computing analytical rankings.
2. **`CASE` inside `SUM()`**: Evaluates status flags conditionally (e.g. counting resolved vs active tickets without filtering out rows).
3. **`RANK() OVER (ORDER BY ...)`**: Calculates global company rank with ties handling.
4. **`DENSE_RANK() OVER (PARTITION BY team_name ...)`**: Resets rankings per support team partition.
5. **`NULLIF(..., 0)`**: Prevents Division by Zero errors gracefully in SQL."""
    },
    {
        "id": "q2_recurring_problems_having",
        "title": "2. Recurring Problem & Root Cause Detection (GROUP BY + HAVING)",
        "category": "Aggregations & Filtering",
        "concepts": ["GROUP BY", "HAVING", "Aggregate Functions (COUNT, SUM, AVG)", "Subquery in SELECT", "CASE Expression"],
        "business_question": "Which IT categories generate the highest incident volume, severe outages, and repeated reopens across the company?",
        "sql": """SELECT 
    category,
    COUNT(*) AS incident_frequency,
    SUM(CASE WHEN priority = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) AS high_count,
    SUM(CASE WHEN reopen_count > 0 THEN 1 ELSE 0 END) AS reopened_count,
    ROUND(AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END), 2) AS avg_csat,
    ROUND((COUNT(*) * 100.0) / (SELECT COUNT(*) FROM tickets), 2) AS share_of_total_load_pct
FROM tickets
GROUP BY category
HAVING COUNT(*) >= 1
ORDER BY incident_frequency DESC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **`GROUP BY category`**: Aggregates all ticket rows into distinct incident categories.
2. **`HAVING COUNT(*) >= 1`**: Filters grouped results on post-aggregation conditions.
3. **Subquery in `SELECT` (`(SELECT COUNT(*) FROM tickets)`)**: Computes the overall company ticket volume inline to calculate percentage share per category.
4. **Conditional `SUM(CASE ...)`**: Categorizes volume into Critical and High severity tiers."""
    },
    {
        "id": "q3_overloaded_teams_capacity",
        "title": "3. Team Workload & Capacity Bottleneck Analysis",
        "category": "Capacity & Workload",
        "concepts": ["LEFT JOIN", "Multiple Aggregates", "Nested CASE Expressions", "DISTINCT in COUNT", "NULLIF"],
        "business_question": "Which support teams are currently experiencing capacity bottlenecks or critical overload?",
        "sql": """SELECT 
    st.team_id,
    st.name AS team_name,
    st.specialization,
    COUNT(DISTINCT a.agent_id) AS active_agent_count,
    COALESCE(SUM(a.max_active_tickets), 0) AS total_team_capacity,
    COUNT(t.ticket_id) AS total_lifetime_tickets,
    SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS current_active_workload,
    ROUND(
        (SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 100.0) / 
        NULLIF(SUM(a.max_active_tickets), 0), 1
    ) AS capacity_utilization_pct,
    CASE 
        WHEN (SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 1.0) / NULLIF(SUM(a.max_active_tickets), 1) >= 0.80 
            THEN '🚨 CRITICAL OVERLOAD'
        WHEN (SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 1.0) / NULLIF(SUM(a.max_active_tickets), 1) >= 0.60 
            THEN '⚠️ HIGH LOAD'
        ELSE '🟢 BALANCED'
    END AS workload_health_status
FROM support_teams st
LEFT JOIN agents a ON st.team_id = a.team_id
LEFT JOIN tickets t ON st.team_id = t.team_id
GROUP BY st.team_id, st.name, st.specialization
ORDER BY capacity_utilization_pct DESC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **`COUNT(DISTINCT a.agent_id)`**: Accurately counts unique agents even after joining with the one-to-many tickets table.
2. **`COALESCE(SUM(...), 0)`**: Handles NULL cases if a team has no registered agents.
3. **Multi-condition `CASE WHEN ... THEN ... ELSE`**: Derives a categorical operational health metric based on mathematical threshold ratios."""
    },
    {
        "id": "q4_department_demand_matrix",
        "title": "4. Department-Wise Incident Demand & Outage Share",
        "category": "Relational Joins & Subqueries",
        "concepts": ["LEFT JOIN", "GROUP BY", "Subqueries", "CASE Expressions", "ORDER BY"],
        "business_question": "Which business units create the highest demand on IT and generate the most severe disruptions?",
        "sql": """SELECT 
    d.department_id,
    d.name AS department_name,
    d.code AS department_code,
    d.head_name,
    COUNT(t.ticket_id) AS total_requests,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_p1_tickets,
    SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_p2_tickets,
    SUM(CASE WHEN t.status IN ('Open', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) AS open_backlog,
    SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_tickets,
    ROUND(
        (COUNT(t.ticket_id) * 100.0) / (SELECT COUNT(*) FROM tickets), 2
    ) AS company_demand_share_pct
FROM departments d
LEFT JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.department_id, d.name, d.code, d.head_name
ORDER BY total_requests DESC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **`LEFT JOIN` on `departments` and `tickets`**: Ensures departments with zero tickets are still preserved and displayed with 0 count.
2. **Correlated share computation**: Employs an inline subquery in the projection clause to compute relative percentage load."""
    },
    {
        "id": "q5_sla_breach_matrix",
        "title": "5. SLA Compliance & Policy Threshold Matrix",
        "category": "Conditional Logic & Pivoting",
        "concepts": ["INNER JOIN / LEFT JOIN", "GROUP BY", "CASE Expressions in ORDER BY", "SLA Target Comparison"],
        "business_question": "What is the exact SLA compliance rate and breach distribution across each priority tier?",
        "sql": """SELECT 
    t.priority,
    sp.response_time_hours AS target_response_hrs,
    sp.resolution_time_hours AS target_resolution_hrs,
    COUNT(*) AS total_tickets,
    SUM(CASE WHEN t.sla_breached = 0 THEN 1 ELSE 0 END) AS within_sla_count,
    SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_count,
    ROUND((SUM(CASE WHEN t.sla_breached = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) AS sla_compliance_rate_pct,
    ROUND((SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1) AS sla_breach_rate_pct
FROM tickets t
LEFT JOIN sla_policies sp ON t.priority = sp.priority
GROUP BY t.priority, sp.response_time_hours, sp.resolution_time_hours
ORDER BY 
    CASE t.priority 
        WHEN 'Critical' THEN 1 
        WHEN 'High' THEN 2 
        WHEN 'Medium' THEN 3 
        WHEN 'Low' THEN 4 
    END ASC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **Custom Ordering with `CASE` in `ORDER BY`**: Enforces strict business hierarchy sorting (Critical -> High -> Medium -> Low) instead of alphabetical order.
2. **`LEFT JOIN sla_policies`**: Enriches ticket aggregates with governing policy thresholds."""
    },
    {
        "id": "q6_reopened_tickets_defects",
        "title": "6. Reopened Tickets & Resolution Quality Defect Analysis",
        "category": "Defect & Reopen Analysis",
        "concepts": ["Multiple INNER/LEFT JOINs", "WHERE Filtering", "ORDER BY Multi-Column", "Root Cause Tracking"],
        "business_question": "Which tickets were reopened multiple times, indicating incomplete or poor first-time resolution?",
        "sql": """SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    t.category,
    t.priority,
    t.reopen_count,
    req.full_name AS requester_name,
    d.name AS department_name,
    ag_u.full_name AS assigned_agent,
    t.status,
    t.root_cause,
    t.resolution_notes
FROM tickets t
JOIN users req ON t.requester_id = req.user_id
LEFT JOIN departments d ON t.department_id = d.department_id
LEFT JOIN agents ag ON t.assigned_agent_id = ag.agent_id
LEFT JOIN users ag_u ON ag.user_id = ag_u.user_id
WHERE t.reopen_count > 0 OR t.status = 'Reopened'
ORDER BY t.reopen_count DESC, t.ticket_id DESC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **Multi-Table Relational Navigation**: Joins `tickets`, `users` (requester), `departments`, `agents`, and `users` (agent).
2. **Defect Filtering (`WHERE reopen_count > 0`)**: Isolates tickets that bounced back to identify recurring procedural failures."""
    },
    {
        "id": "q7_monthly_trend_cohorts",
        "title": "7. Multi-Period Historical Trend & Resolution Velocity",
        "category": "Date & Timestamp Analytics",
        "concepts": ["Date Extraction (`SUBSTR` / `strftime`)", "GROUP BY Date Period", "Multi-Metric Aggregations", "Running Trend"],
        "business_question": "How have ticket creation volume, resolution rates, and SLA breaches trended month-over-month?",
        "sql": """SELECT 
    SUBSTR(created_at, 1, 7) AS month_year,
    COUNT(*) AS tickets_created,
    SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS tickets_resolved,
    SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) AS sla_breaches,
    SUM(CASE WHEN reopen_count > 0 THEN 1 ELSE 0 END) AS total_reopens,
    ROUND(AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END), 2) AS monthly_avg_csat,
    ROUND(
        (SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1
    ) AS monthly_resolution_rate_pct
FROM tickets
GROUP BY SUBSTR(created_at, 1, 7)
ORDER BY month_year ASC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **Date Truncation (`SUBSTR(created_at, 1, 7)`)**: Groups timestamps by year and month (e.g. `2026-09`, `2026-10`).
2. **Cohort Velocity Metrics**: Measures resolution speed and CSAT consistency over time."""
    },
    {
        "id": "q8_higher_than_average_dept",
        "title": "8. Departments Exceeding Company Average Demand (Correlated Subquery)",
        "category": "Subqueries",
        "concepts": ["Correlated Subquery", "HAVING with Nested Subquery", "GROUP BY", "Aggregate Comparison"],
        "business_question": "Which departments generate more tickets than the average department volume across the entire organization?",
        "sql": """SELECT 
    d.name AS department_name,
    COUNT(t.ticket_id) AS dept_ticket_count,
    ROUND((SELECT COUNT(*) * 1.0 / COUNT(DISTINCT department_id) FROM tickets), 1) AS company_dept_average
FROM departments d
JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.name
HAVING COUNT(t.ticket_id) > (
    SELECT COUNT(*) * 1.0 / COUNT(DISTINCT department_id) 
    FROM tickets
)
ORDER BY dept_ticket_count DESC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **`HAVING` with Subquery**: Filters groups whose aggregate count strictly exceeds the dynamic company-wide average calculated in the subquery.
2. **Dynamic Baseline Calculation**: Eliminates hardcoded thresholds."""
    },
    {
        "id": "q9_agent_workload_ntile",
        "title": "9. Agent Workload Distribution & Quartile Segmentation (NTILE)",
        "category": "Window Functions & CTEs",
        "concepts": ["NTILE() OVER()", "ROW_NUMBER() OVER()", "CTE", "Agent Segmentation"],
        "business_question": "How are support agents segmented into workload quartiles (Top 25% busiest down to lightest load)?",
        "sql": """WITH agent_workload AS (
    SELECT 
        a.agent_id,
        u.full_name AS agent_name,
        st.name AS team_name,
        COUNT(t.ticket_id) AS total_assigned,
        SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_load
    FROM agents a
    JOIN users u ON a.user_id = u.user_id
    LEFT JOIN support_teams st ON a.team_id = st.team_id
    LEFT JOIN tickets t ON a.agent_id = t.assigned_agent_id
    GROUP BY a.agent_id, u.full_name, st.name
)
SELECT 
    agent_id,
    agent_name,
    team_name,
    total_assigned,
    active_load,
    NTILE(4) OVER (ORDER BY active_load DESC) AS workload_quartile,
    ROW_NUMBER() OVER (PARTITION BY team_name ORDER BY active_load DESC) AS team_workload_rank
FROM agent_workload
ORDER BY active_load DESC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **`NTILE(4) OVER (ORDER BY active_load DESC)`**: Divides ranked agents evenly into 4 quartiles (Q1 = heaviest load, Q4 = lightest load).
2. **`ROW_NUMBER() OVER (PARTITION BY ...)`**: Assigns unique 1..N sequence within each support team."""
    },
    {
        "id": "q10_sla_countdown_query",
        "title": "10. Real-Time SLA Countdown & Breach Flagging",
        "category": "Date & SLA Math",
        "concepts": ["Date Arithmetic", "CASE Expression Status Flagging", "CURRENT_TIMESTAMP Comparison"],
        "business_question": "What is the live SLA countdown, elapsed time, and urgency flag for all open tickets?",
        "sql": """SELECT 
    t.ticket_number,
    t.title,
    t.priority,
    t.status,
    t.created_at,
    t.sla_due_date,
    req.full_name AS requester_name,
    ag_u.full_name AS assigned_agent,
    CASE 
        WHEN t.status IN ('Resolved', 'Closed') AND t.sla_breached = 0 THEN '✅ SLA Met'
        WHEN t.status IN ('Resolved', 'Closed') AND t.sla_breached = 1 THEN '❌ Breached (Resolved Late)'
        WHEN t.sla_due_date < CURRENT_TIMESTAMP THEN '🚨 OVERDUE BREACH'
        ELSE '⏱️ Within Target'
    END AS sla_urgency_status
FROM tickets t
JOIN users req ON t.requester_id = req.user_id
LEFT JOIN agents ag ON t.assigned_agent_id = ag.agent_id
LEFT JOIN users ag_u ON ag.user_id = ag_u.user_id
WHERE t.status NOT IN ('Resolved', 'Closed')
ORDER BY t.sla_due_date ASC;""",
        "explanation": """### SQL Concepts Breakdown:
1. **`CURRENT_TIMESTAMP` Comparison**: Evaluates overdue states in real-time within the database engine.
2. **Multi-branch `CASE`**: Classifies tickets into actionable operational statuses."""
    }
]

def get_all_query_catalog():
    return SQL_QUERIES_CATALOG

def get_query_by_id(query_id: str):
    for q in SQL_QUERIES_CATALOG:
        if q["id"] == query_id:
            return q
    return None
