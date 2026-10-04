-- ==========================================================
-- IT Helpdesk & Ticket Management System - Stored Procedures
-- Member 3: SQL Analytics & Business Intelligence
-- ==========================================================

USE it_helpdesk_db;

DELIMITER //

-- 1. Get Agent Performance Metrics
-- Retrieves performance statistics for all agents or a specific agent
DROP PROCEDURE IF EXISTS get_agent_performance //
CREATE PROCEDURE get_agent_performance(IN p_agent_id INT)
BEGIN
    IF p_agent_id IS NULL OR p_agent_id = 0 THEN
        SELECT 
            apv.*,
            DENSE_RANK() OVER (ORDER BY apv.resolved_tickets DESC, apv.sla_compliance_pct DESC) AS performance_rank
        FROM agent_performance_view apv
        ORDER BY performance_rank;
    ELSE
        SELECT 
            apv.*,
            DENSE_RANK() OVER (ORDER BY apv.resolved_tickets DESC, apv.sla_compliance_pct DESC) AS performance_rank
        FROM agent_performance_view apv
        WHERE apv.agent_id = p_agent_id;
    END IF;
END //

-- 2. Get Department Summary
-- Returns aggregated ticket counts, breach rates, and resolution speed per department
DROP PROCEDURE IF EXISTS get_department_summary //
CREATE PROCEDURE get_department_summary()
BEGIN
    SELECT 
        department_id,
        department_name,
        department_code,
        total_tickets,
        open_tickets,
        in_progress_tickets,
        resolved_tickets,
        critical_tickets,
        avg_resolution_hours,
        sla_compliance_pct,
        CASE 
            WHEN sla_compliance_pct < 80 THEN 'Needs Attention'
            WHEN total_tickets > 20 THEN 'High Activity'
            ELSE 'Healthy'
        END AS department_health_status
    FROM department_ticket_view
    ORDER BY total_tickets DESC;
END //

-- 3. Get SLA Breaches
-- Extracts all tickets that have breached or are currently breaching SLA deadlines
DROP PROCEDURE IF EXISTS get_sla_breaches //
CREATE PROCEDURE get_sla_breaches()
BEGIN
    SELECT 
        ticket_id,
        ticket_number,
        title,
        priority,
        status,
        department_name,
        assigned_agent,
        created_at,
        resolution_deadline,
        resolved_at,
        sla_status,
        breach_minutes,
        ROUND(breach_minutes / 60.0, 1) AS breach_hours
    FROM sla_breach_view 
    WHERE sla_status IN ('Resolved Past SLA', 'Currently Breached')
    ORDER BY breach_minutes DESC;
END //

-- 4. Get Monthly Ticket Report
-- Returns monthly ticket distribution and resolution velocity
DROP PROCEDURE IF EXISTS get_monthly_ticket_report //
CREATE PROCEDURE get_monthly_ticket_report(IN p_year_month VARCHAR(7))
BEGIN
    IF p_year_month IS NULL OR p_year_month = '' THEN
        SELECT * FROM monthly_ticket_summary_view
        ORDER BY ticket_month DESC, ticket_count DESC;
    ELSE
        SELECT * FROM monthly_ticket_summary_view 
        WHERE ticket_month = p_year_month
        ORDER BY ticket_count DESC;
    END IF;
END //

-- 5. Get Agent & Team Workload Analysis
-- Analyzes active queue volume and pinpoints overloaded agents
DROP PROCEDURE IF EXISTS get_workload_analysis //
CREATE PROCEDURE get_workload_analysis()
BEGIN
    SELECT 
        agent_id,
        agent_name,
        team_name,
        is_available,
        open_ticket_count,
        critical_ticket_count,
        high_ticket_count,
        workload_status
    FROM open_ticket_workload_view
    ORDER BY open_ticket_count DESC;
END //

-- 6. Get Recurring Issues
-- Pinpoints high frequency problem types requiring system-level remediation
DROP PROCEDURE IF EXISTS get_recurring_issues //
CREATE PROCEDURE get_recurring_issues(IN p_min_count INT)
BEGIN
    SET p_min_count = COALESCE(p_min_count, 1);
    SELECT 
        category_id,
        category_name,
        occurrence_count,
        critical_occurrences,
        high_occurrences,
        total_reopenings,
        avg_resolution_hours
    FROM recurring_issue_view
    WHERE occurrence_count >= p_min_count
    ORDER BY occurrence_count DESC;
END //

-- 7. Get Reopened Ticket Analysis
-- Analyzes reopened incident patterns, associated agents and departments
DROP PROCEDURE IF EXISTS get_reopened_ticket_analysis //
CREATE PROCEDURE get_reopened_ticket_analysis()
BEGIN
    SELECT 
        ticket_id,
        ticket_number,
        title,
        category_name,
        department_name,
        assigned_agent,
        reopened_count,
        current_status,
        created_at,
        resolved_at,
        total_lifecycle_hours
    FROM reopened_ticket_view
    ORDER BY reopened_count DESC, total_lifecycle_hours DESC;
END //

DELIMITER ;
