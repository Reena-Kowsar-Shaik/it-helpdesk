-- ==========================================================
-- IT Helpdesk & Ticket Management System - SQL Views
-- Member 3: SQL Analytics & Business Intelligence
-- ==========================================================

USE it_helpdesk_db;

-- 1. Agent Performance Summary View
-- Computes assigned, resolved, active queue, avg resolution time, SLA %, and reopened tickets per agent
CREATE OR REPLACE VIEW agent_performance_view AS
SELECT 
    sa.agent_id,
    sa.full_name AS agent_name,
    COALESCE(st.name, 'General Support') AS team_name,
    COUNT(t.ticket_id) AS total_assigned_tickets,
    SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved_tickets,
    SUM(CASE WHEN t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED') THEN 1 ELSE 0 END) AS active_tickets,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_resolution_hours,
    ROUND(
        (SUM(CASE 
            WHEN t.status IN ('RESOLVED', 'CLOSED') 
                 AND (t.resolved_at <= t.resolution_deadline OR t.resolution_deadline IS NULL) 
            THEN 1 ELSE 0 END) / 
         NULLIF(SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END), 0)
        ) * 100, 
    1) AS sla_compliance_pct,
    COALESCE(SUM(t.reopened_count), 0) AS total_reopened_count
FROM support_agents sa
LEFT JOIN support_teams st ON sa.team_id = st.team_id
LEFT JOIN tickets t ON sa.agent_id = t.assigned_agent_id
GROUP BY sa.agent_id, sa.full_name, st.name;

-- 2. Department Ticket Volume and Health View
-- Aggregates ticket volume, backlog, resolution time and compliance by department
CREATE OR REPLACE VIEW department_ticket_view AS
SELECT 
    d.department_id,
    d.name AS department_name,
    d.code AS department_code,
    COUNT(t.ticket_id) AS total_tickets,
    SUM(CASE WHEN t.status IN ('OPEN', 'ASSIGNED') THEN 1 ELSE 0 END) AS open_tickets,
    SUM(CASE WHEN t.status = 'IN PROGRESS' THEN 1 ELSE 0 END) AS in_progress_tickets,
    SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved_tickets,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_tickets,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_resolution_hours,
    ROUND(
        (SUM(CASE 
            WHEN (t.resolved_at IS NOT NULL AND t.resolved_at <= t.resolution_deadline)
                 OR (t.resolved_at IS NULL AND NOW() <= t.resolution_deadline)
                 OR t.resolution_deadline IS NULL 
            THEN 1 ELSE 0 END) / 
         NULLIF(COUNT(t.ticket_id), 0)
        ) * 100, 
    1) AS sla_compliance_pct
FROM departments d
LEFT JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.department_id, d.name, d.code;

-- 3. SLA Breach Monitoring View
-- Identifies tickets that breached deadline, are at imminent risk (<1 hour), or are within SLA
CREATE OR REPLACE VIEW sla_breach_view AS
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    t.priority,
    t.status,
    d.name AS department_name,
    COALESCE(sa.full_name, 'Unassigned') AS assigned_agent,
    t.created_at,
    t.resolution_deadline,
    t.resolved_at,
    CASE 
        WHEN t.status IN ('RESOLVED', 'CLOSED') AND t.resolved_at > t.resolution_deadline THEN 'Resolved Past SLA'
        WHEN t.status NOT IN ('RESOLVED', 'CLOSED') AND NOW() > t.resolution_deadline THEN 'Currently Breached'
        WHEN t.status NOT IN ('RESOLVED', 'CLOSED') AND TIMESTAMPDIFF(MINUTE, NOW(), t.resolution_deadline) BETWEEN 0 AND 60 THEN 'At Risk (<1 hr)'
        ELSE 'Within SLA'
    END AS sla_status,
    TIMESTAMPDIFF(MINUTE, t.resolution_deadline, COALESCE(t.resolved_at, NOW())) AS breach_minutes
FROM tickets t
JOIN departments d ON t.department_id = d.department_id
LEFT JOIN support_agents sa ON t.assigned_agent_id = sa.agent_id
WHERE t.resolution_deadline IS NOT NULL;

-- 4. Open Ticket Workload View
-- Tracks live open ticket counts and categorizes load as Overloaded, Moderate, or Optimal
CREATE OR REPLACE VIEW open_ticket_workload_view AS
SELECT 
    sa.agent_id,
    sa.full_name AS agent_name,
    COALESCE(st.name, 'General Support') AS team_name,
    sa.is_available,
    COUNT(t.ticket_id) AS open_ticket_count,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_ticket_count,
    SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_ticket_count,
    CASE 
        WHEN COUNT(t.ticket_id) >= 10 THEN 'Overloaded'
        WHEN COUNT(t.ticket_id) >= 5 THEN 'Moderate'
        ELSE 'Optimal'
    END AS workload_status
FROM support_agents sa
LEFT JOIN support_teams st ON sa.team_id = st.team_id
LEFT JOIN tickets t ON sa.agent_id = t.assigned_agent_id 
    AND t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED')
GROUP BY sa.agent_id, sa.full_name, st.name, sa.is_available;

-- 5. Monthly Ticket Summary View
-- Time-series aggregation for ticket generation and resolution trends by month and category
CREATE OR REPLACE VIEW monthly_ticket_summary_view AS
SELECT 
    DATE_FORMAT(t.created_at, '%Y-%m') AS ticket_month,
    c.name AS category_name,
    t.priority,
    COUNT(t.ticket_id) AS ticket_count,
    SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved_count,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_resolution_hours
FROM tickets t
JOIN categories c ON t.category_id = c.category_id
GROUP BY DATE_FORMAT(t.created_at, '%Y-%m'), c.name, t.priority
ORDER BY ticket_month DESC, ticket_count DESC;

-- 6. Recurring Issues Frequency View
-- Highlights technical problem hotspots requiring permanent IT infrastructure or policy solutions
CREATE OR REPLACE VIEW recurring_issue_view AS
SELECT 
    c.category_id,
    c.name AS category_name,
    COUNT(t.ticket_id) AS occurrence_count,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_occurrences,
    SUM(CASE WHEN t.priority = 'High' THEN 1 ELSE 0 END) AS high_occurrences,
    COALESCE(SUM(t.reopened_count), 0) AS total_reopenings,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_resolution_hours
FROM categories c
LEFT JOIN tickets t ON c.category_id = t.category_id
GROUP BY c.category_id, c.name
ORDER BY occurrence_count DESC;

-- 7. Reopened Ticket Audit View
-- Analyzes tickets that required reopening to identify incomplete fixes or recurring breakdowns
CREATE OR REPLACE VIEW reopened_ticket_view AS
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    c.name AS category_name,
    d.name AS department_name,
    COALESCE(sa.full_name, 'Unassigned') AS assigned_agent,
    t.reopened_count,
    t.status AS current_status,
    t.created_at,
    t.resolved_at,
    TIMESTAMPDIFF(HOUR, t.created_at, COALESCE(t.resolved_at, NOW())) AS total_lifecycle_hours
FROM tickets t
JOIN categories c ON t.category_id = c.category_id
JOIN departments d ON t.department_id = d.department_id
LEFT JOIN support_agents sa ON t.assigned_agent_id = sa.agent_id
WHERE t.reopened_count > 0;
