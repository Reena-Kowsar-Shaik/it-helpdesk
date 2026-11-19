"""
Advanced SQL Queries Library for IT Helpdesk & Service Intelligence.
Includes CTEs, Window Functions, Aggregate Aggregations, Subqueries,
and Case Expressions compatible with MySQL 8.0+ and SQLite 3.25+.
"""

# 1. EXECUTIVE KPI SUMMARY
QUERY_KPI_SUMMARY = """
SELECT 
    COUNT(*) AS total_tickets,
    SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_tickets,
    SUM(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) AS assigned_tickets,
    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_tickets,
    SUM(CASE WHEN status = 'Pending Customer' THEN 1 ELSE 0 END) AS pending_customer_tickets,
    SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS resolved_tickets,
    SUM(CASE WHEN status = 'Reopened' OR reopen_count > 0 THEN 1 ELSE 0 END) AS reopened_tickets,
    SUM(CASE WHEN priority = 'Critical' AND status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_critical,
    SUM(CASE WHEN sla_breached = 1 THEN 1 ELSE 0 END) AS sla_breached_count,
    ROUND(AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END), 2) AS avg_csat_score,
    ROUND(
        (SUM(CASE WHEN sla_breached = 0 AND status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 100.0) / 
        NULLIF(SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END), 0), 2
    ) AS sla_compliance_pct
FROM tickets;
"""

# 2. AGENT PERFORMANCE & RANKING (WINDOW FUNCTIONS + CTE)
QUERY_AGENT_RANKINGS = """
WITH agent_stats AS (
    SELECT 
        a.agent_id,
        u.full_name AS agent_name,
        u.email AS agent_email,
        a.tier,
        st.name AS team_name,
        a.status AS current_status,
        a.max_active_tickets,
        COUNT(t.ticket_id) AS total_assigned,
        SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS tickets_resolved,
        SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_tickets,
        SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_tickets,
        SUM(CASE WHEN t.reopen_count > 0 THEN 1 ELSE 0 END) AS reopened_tickets,
        ROUND(AVG(CASE WHEN t.satisfaction_rating IS NOT NULL THEN t.satisfaction_rating END), 2) AS avg_csat,
        ROUND(AVG(CASE 
            WHEN t.resolved_at IS NOT NULL THEN 
                (strftime('%s', t.resolved_at) - strftime('%s', t.created_at)) / 3600.0
            ELSE NULL 
        END), 2) AS avg_resolution_hours
    FROM agents a
    JOIN users u ON a.user_id = u.user_id
    LEFT JOIN support_teams st ON a.team_id = st.team_id
    LEFT JOIN tickets t ON a.agent_id = t.assigned_agent_id
    GROUP BY a.agent_id, u.full_name, u.email, a.tier, st.name, a.status, a.max_active_tickets
)
SELECT 
    agent_id,
    agent_name,
    team_name,
    tier,
    current_status,
    total_assigned,
    tickets_resolved,
    active_tickets,
    max_active_tickets,
    breached_tickets,
    reopened_tickets,
    avg_csat,
    COALESCE(avg_resolution_hours, 0) AS avg_resolution_hours,
    ROUND(
        (tickets_resolved * 100.0) / NULLIF(total_assigned, 0), 1
    ) AS resolution_rate_pct,
    ROUND(
        ((tickets_resolved - breached_tickets) * 100.0) / NULLIF(tickets_resolved, 0), 1
    ) AS sla_compliance_pct,
    RANK() OVER (ORDER BY tickets_resolved DESC, avg_csat DESC) AS performance_rank,
    DENSE_RANK() OVER (PARTITION BY team_name ORDER BY tickets_resolved DESC) AS team_rank
FROM agent_stats
ORDER BY performance_rank ASC;
"""

# MySQL Alternative for Agent Rankings using TIMESTAMPDIFF
QUERY_AGENT_RANKINGS_MYSQL = """
WITH agent_stats AS (
    SELECT 
        a.agent_id,
        u.full_name AS agent_name,
        u.email AS agent_email,
        a.tier,
        st.name AS team_name,
        a.status AS current_status,
        a.max_active_tickets,
        COUNT(t.ticket_id) AS total_assigned,
        SUM(CASE WHEN t.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS tickets_resolved,
        SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_tickets,
        SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_tickets,
        SUM(CASE WHEN t.reopen_count > 0 THEN 1 ELSE 0 END) AS reopened_tickets,
        ROUND(AVG(CASE WHEN t.satisfaction_rating IS NOT NULL THEN t.satisfaction_rating END), 2) AS avg_csat,
        ROUND(AVG(CASE 
            WHEN t.resolved_at IS NOT NULL THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0
            ELSE NULL 
        END), 2) AS avg_resolution_hours
    FROM agents a
    JOIN users u ON a.user_id = u.user_id
    LEFT JOIN support_teams st ON a.team_id = st.team_id
    LEFT JOIN tickets t ON a.agent_id = t.assigned_agent_id
    GROUP BY a.agent_id, u.full_name, u.email, a.tier, st.name, a.status, a.max_active_tickets
)
SELECT 
    agent_id,
    agent_name,
    team_name,
    tier,
    current_status,
    total_assigned,
    tickets_resolved,
    active_tickets,
    max_active_tickets,
    breached_tickets,
    reopened_tickets,
    avg_csat,
    COALESCE(avg_resolution_hours, 0) AS avg_resolution_hours,
    ROUND((tickets_resolved * 100.0) / NULLIF(total_assigned, 0), 1) AS resolution_rate_pct,
    ROUND(((tickets_resolved - breached_tickets) * 100.0) / NULLIF(tickets_resolved, 0), 1) AS sla_compliance_pct,
    RANK() OVER (ORDER BY tickets_resolved DESC, avg_csat DESC) AS performance_rank,
    DENSE_RANK() OVER (PARTITION BY team_name ORDER BY tickets_resolved DESC) AS team_rank
FROM agent_stats
ORDER BY performance_rank ASC;
"""

# 3. DEPARTMENT-WISE TICKET DEMAND & LOAD ANALYSIS
QUERY_DEPARTMENT_LOAD = """
SELECT 
    d.department_id,
    d.name AS department_name,
    d.code AS department_code,
    d.head_name,
    COUNT(t.ticket_id) AS total_requests,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_tickets,
    SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_tickets,
    SUM(CASE WHEN t.status IN ('Open', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) AS pending_tickets,
    SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_tickets,
    ROUND(
        (COUNT(t.ticket_id) * 100.0) / (SELECT COUNT(*) FROM tickets), 2
    ) AS pct_of_total_company_load
FROM departments d
LEFT JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.department_id, d.name, d.code, d.head_name
ORDER BY total_requests DESC;
"""

# 4. RECURRING IT PROBLEMS & ROOT CAUSE ANALYSIS (GROUP BY + HAVING)
QUERY_RECURRING_PROBLEMS = """
SELECT 
    category,
    COUNT(*) AS incident_frequency,
    SUM(CASE WHEN priority IN ('Critical', 'High') THEN 1 ELSE 0 END) AS severe_incidents,
    SUM(CASE WHEN reopen_count > 0 THEN 1 ELSE 0 END) AS reopened_count,
    ROUND(AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END), 2) AS avg_rating,
    ROUND(
        (COUNT(*) * 100.0) / (SELECT COUNT(*) FROM tickets), 2
    ) AS share_of_incidents_pct
FROM tickets
GROUP BY category
HAVING COUNT(*) >= 1
ORDER BY incident_frequency DESC;
"""

# 5. OVERLOADED TEAMS & CAPACITY BOTTLENECK ANALYSIS
QUERY_TEAM_WORKLOAD = """
SELECT 
    st.team_id,
    st.name AS team_name,
    st.specialization,
    COUNT(DISTINCT a.agent_id) AS active_agent_count,
    SUM(a.max_active_tickets) AS total_team_capacity,
    COUNT(t.ticket_id) AS total_assigned_tickets,
    SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS active_ticket_workload,
    ROUND(
        (SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 100.0) / 
        NULLIF(SUM(a.max_active_tickets), 0), 1
    ) AS capacity_utilization_pct,
    CASE 
        WHEN (SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 1.0) / NULLIF(SUM(a.max_active_tickets), 1) >= 0.85 
            THEN 'CRITICAL OVERLOAD'
        WHEN (SUM(CASE WHEN t.status NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 1.0) / NULLIF(SUM(a.max_active_tickets), 1) >= 0.65 
            THEN 'HIGH LOAD'
        ELSE 'BALANCED'
    END AS workload_status
FROM support_teams st
LEFT JOIN agents a ON st.team_id = a.team_id
LEFT JOIN tickets t ON st.team_id = t.team_id
GROUP BY st.team_id, st.name, st.specialization
ORDER BY capacity_utilization_pct DESC;
"""

# 6. SLA BREACH & RESOLUTION TIME INTELLIGENCE
QUERY_SLA_ANALYSIS = """
SELECT 
    t.priority,
    COUNT(*) AS total_tickets,
    SUM(CASE WHEN t.sla_breached = 1 THEN 1 ELSE 0 END) AS breached_count,
    SUM(CASE WHEN t.sla_breached = 0 THEN 1 ELSE 0 END) AS within_sla_count,
    ROUND(
        (SUM(CASE WHEN t.sla_breached = 0 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 1
    ) AS sla_met_pct,
    sp.response_time_hours AS target_response_hours,
    sp.resolution_time_hours AS target_resolution_hours
FROM tickets t
LEFT JOIN sla_policies sp ON t.priority = sp.priority
GROUP BY t.priority, sp.response_time_hours, sp.resolution_time_hours
ORDER BY 
    CASE t.priority 
        WHEN 'Critical' THEN 1 
        WHEN 'High' THEN 2 
        WHEN 'Medium' THEN 3 
        WHEN 'Low' THEN 4 
    END;
"""

# 7. REOPENED TICKETS & RESOLUTION DEFECT ANALYSIS
QUERY_REOPENED_ANALYSIS = """
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    t.category,
    t.priority,
    t.reopen_count,
    u.full_name AS requester_name,
    ag_u.full_name AS assigned_agent,
    t.status,
    t.root_cause,
    t.resolution_notes
FROM tickets t
JOIN users u ON t.requester_id = u.user_id
LEFT JOIN agents ag ON t.assigned_agent_id = ag.agent_id
LEFT JOIN users ag_u ON ag.user_id = ag_u.user_id
WHERE t.reopen_count > 0 OR t.status = 'Reopened'
ORDER BY t.reopen_count DESC, t.ticket_id DESC;
"""

# 8. TICKETS DETAILED LIST WITH RICH JOINS
QUERY_ALL_TICKETS = """
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    t.description,
    t.category,
    t.priority,
    t.status,
    t.created_at,
    t.sla_due_date,
    t.sla_breached,
    t.reopen_count,
    t.satisfaction_rating,
    t.resolution_notes,
    req.full_name AS requester_name,
    req.email AS requester_email,
    d.name AS department_name,
    st.name AS team_name,
    ag_u.full_name AS agent_name,
    ag.tier AS agent_tier
FROM tickets t
JOIN users req ON t.requester_id = req.user_id
LEFT JOIN departments d ON t.department_id = d.department_id
LEFT JOIN support_teams st ON t.team_id = st.team_id
LEFT JOIN agents ag ON t.assigned_agent_id = ag.agent_id
LEFT JOIN users ag_u ON ag.user_id = ag_u.user_id
ORDER BY t.ticket_id DESC;
"""
