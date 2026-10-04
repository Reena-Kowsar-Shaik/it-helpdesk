-- ==========================================================
-- IT Helpdesk & Ticket Management System - Advanced SQL Analytics Showcase
-- Member 3: SQL Analytics & Business Intelligence Specialist
--
-- This script contains production-grade SQL queries demonstrating:
-- 1. Multi-Table JOINs
-- 2. GROUP BY & HAVING Clauses
-- 3. Subqueries & Correlated Subqueries
-- 4. Common Table Expressions (CTEs)
-- 5. Analytical Window Functions (RANK, DENSE_RANK, ROW_NUMBER, PARTITION BY)
-- 6. Date & Time Analytics (TIMESTAMPDIFF, DATE_FORMAT)
-- 7. Conditional Aggregations with CASE
-- ==========================================================

USE it_helpdesk_db;

-- ==========================================================
-- QUERY 1: Multi-Table JOIN with Conditional Aggregation
-- Purpose: Department-wise Ticket Volume, Active Backlog & SLA Compliance
-- ==========================================================
SELECT 
    d.department_id,
    d.name AS department_name,
    d.code AS department_code,
    COUNT(t.ticket_id) AS total_tickets,
    SUM(CASE WHEN t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED') THEN 1 ELSE 0 END) AS active_backlog,
    SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved_count,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
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
GROUP BY d.department_id, d.name, d.code
ORDER BY total_tickets DESC;

-- ==========================================================
-- QUERY 2: GROUP BY with HAVING Clause
-- Purpose: Identify high-risk departments where incident volume exceeds 2 tickets
--          AND average resolution time exceeds 2.5 hours
-- ==========================================================
SELECT 
    d.name AS department_name,
    COUNT(t.ticket_id) AS total_incidents,
    ROUND(AVG(TIMESTAMPDIFF(MINUTE, t.created_at, COALESCE(t.resolved_at, NOW())) / 60.0), 2) AS avg_duration_hours,
    SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_incidents
FROM departments d
JOIN tickets t ON d.department_id = t.department_id
GROUP BY d.name
HAVING COUNT(t.ticket_id) >= 2 
   AND avg_duration_hours > 2.0
ORDER BY avg_duration_hours DESC;

-- ==========================================================
-- QUERY 3: Window Functions - Agent Performance Leaderboard
-- Purpose: Rank agents using DENSE_RANK() and ROW_NUMBER() based on resolution count and SLA %
-- ==========================================================
SELECT 
    sa.agent_id,
    sa.full_name AS agent_name,
    COALESCE(st.name, 'Unassigned Team') AS team_name,
    COUNT(t.ticket_id) AS total_assigned,
    SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS resolved_count,
    ROUND(AVG(
        CASE 
            WHEN t.resolved_at IS NOT NULL 
            THEN TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0 
            ELSE NULL 
        END
    ), 2) AS avg_res_hours,
    ROUND(
        (SUM(CASE 
            WHEN t.status IN ('RESOLVED', 'CLOSED') 
                 AND (t.resolved_at <= t.resolution_deadline OR t.resolution_deadline IS NULL) 
            THEN 1 ELSE 0 END) / 
         NULLIF(SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END), 0)
        ) * 100, 
    1) AS sla_compliance_pct,
    DENSE_RANK() OVER (
        ORDER BY 
            SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) DESC,
            ROUND(
                (SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') AND (t.resolved_at <= t.resolution_deadline OR t.resolution_deadline IS NULL) THEN 1 ELSE 0 END) / 
                 NULLIF(SUM(CASE WHEN t.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END), 0)) * 100, 1) DESC
    ) AS performance_rank
FROM support_agents sa
LEFT JOIN support_teams st ON sa.team_id = st.team_id
LEFT JOIN tickets t ON sa.agent_id = t.assigned_agent_id
GROUP BY sa.agent_id, sa.full_name, st.name
ORDER BY performance_rank;

-- ==========================================================
-- QUERY 4: Correlated Subquery
-- Purpose: Find tickets whose resolution time was LONGER than their department's average resolution time
-- ==========================================================
SELECT 
    t.ticket_id,
    t.ticket_number,
    t.title,
    d.name AS department_name,
    ROUND(TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0, 2) AS ticket_res_hours,
    ROUND((
        SELECT AVG(TIMESTAMPDIFF(MINUTE, t_inner.created_at, t_inner.resolved_at) / 60.0)
        FROM tickets t_inner
        WHERE t_inner.department_id = t.department_id 
          AND t_inner.resolved_at IS NOT NULL
    ), 2) AS dept_avg_res_hours
FROM tickets t
JOIN departments d ON t.department_id = d.department_id
WHERE t.resolved_at IS NOT NULL
  AND (TIMESTAMPDIFF(MINUTE, t.created_at, t.resolved_at) / 60.0) > (
      SELECT AVG(TIMESTAMPDIFF(MINUTE, t_sub.created_at, t_sub.resolved_at) / 60.0)
      FROM tickets t_sub
      WHERE t_sub.department_id = t.department_id 
        AND t_sub.resolved_at IS NOT NULL
  )
ORDER BY (ticket_res_hours - dept_avg_res_hours) DESC;

-- ==========================================================
-- QUERY 5: Multi-Stage Common Table Expression (CTE)
-- Purpose: Calculate Agent Workload and compare against Team Averages
-- ==========================================================
WITH AgentWorkloadCTE AS (
    SELECT 
        sa.agent_id,
        sa.full_name AS agent_name,
        sa.team_id,
        COUNT(t.ticket_id) AS active_tickets,
        SUM(CASE WHEN t.priority = 'Critical' THEN 1 ELSE 0 END) AS critical_load
    FROM support_agents sa
    LEFT JOIN tickets t ON sa.agent_id = t.assigned_agent_id 
        AND t.status IN ('OPEN', 'ASSIGNED', 'IN PROGRESS', 'REOPENED')
    GROUP BY sa.agent_id, sa.full_name, sa.team_id
),
TeamAverageCTE AS (
    SELECT 
        team_id,
        ROUND(AVG(active_tickets), 1) AS team_avg_active
    FROM AgentWorkloadCTE
    GROUP BY team_id
)
SELECT 
    aw.agent_id,
    aw.agent_name,
    st.name AS team_name,
    aw.active_tickets,
    aw.critical_load,
    ta.team_avg_active,
    CASE 
        WHEN aw.active_tickets >= 10 THEN 'Overloaded (Critical)'
        WHEN aw.active_tickets >= 5 THEN 'Moderate Workload'
        WHEN aw.active_tickets > ta.team_avg_active THEN 'Above Team Average'
        ELSE 'Optimal Capacity'
    END AS capacity_status
FROM AgentWorkloadCTE aw
JOIN support_teams st ON aw.team_id = st.team_id
JOIN TeamAverageCTE ta ON aw.team_id = ta.team_id
ORDER BY aw.active_tickets DESC;

-- ==========================================================
-- QUERY 6: Window Function - Cumulative Monthly Ticket Velocity
-- Purpose: Calculate running cumulative tickets month-over-month
-- ==========================================================
WITH MonthlyTotals AS (
    SELECT 
        DATE_FORMAT(created_at, '%Y-%m') AS report_month,
        COUNT(ticket_id) AS monthly_count,
        SUM(CASE WHEN status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) AS monthly_resolved
    FROM tickets
    GROUP BY DATE_FORMAT(created_at, '%Y-%m')
)
SELECT 
    report_month,
    monthly_count,
    monthly_resolved,
    SUM(monthly_count) OVER (ORDER BY report_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_tickets,
    ROUND((monthly_resolved * 100.0) / NULLIF(monthly_count, 0), 1) AS monthly_resolution_rate_pct
FROM MonthlyTotals
ORDER BY report_month ASC;

-- ==========================================================
-- QUERY 7: Recurring Issue and Root Cause Distribution Analysis
-- Purpose: Pinpoint top recurring incident categories and root cause patterns
-- ==========================================================
SELECT 
    c.name AS category_name,
    COUNT(t.ticket_id) AS total_occurrences,
    COUNT(DISTINCT t.department_id) AS impacted_departments,
    SUM(t.reopened_count) AS reopen_incidents,
    GROUP_CONCAT(DISTINCT tr.root_cause SEPARATOR ' | ') AS documented_root_causes
FROM categories c
JOIN tickets t ON c.category_id = t.category_id
LEFT JOIN ticket_resolutions tr ON t.ticket_id = tr.ticket_id
GROUP BY c.category_id, c.name
ORDER BY total_occurrences DESC;
