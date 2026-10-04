-- ==========================================================
-- IT Helpdesk & Ticket Management System - Stored Procedures
-- ==========================================================

USE it_helpdesk_db;

DELIMITER //

-- 1. Get Agent Performance Metrics
DROP PROCEDURE IF EXISTS get_agent_performance //
CREATE PROCEDURE get_agent_performance(IN p_agent_id INT)
BEGIN
    IF p_agent_id IS NULL OR p_agent_id = 0 THEN
        SELECT * FROM agent_performance_view;
    ELSE
        SELECT * FROM agent_performance_view WHERE agent_id = p_agent_id;
    END IF;
END //

-- 2. Get Department Summary
DROP PROCEDURE IF EXISTS get_department_summary //
CREATE PROCEDURE get_department_summary()
BEGIN
    SELECT * FROM department_ticket_view;
END //

-- 3. Get SLA Breaches
DROP PROCEDURE IF EXISTS get_sla_breaches //
CREATE PROCEDURE get_sla_breaches()
BEGIN
    SELECT * FROM sla_breach_view 
    WHERE sla_status IN ('Resolved Past SLA', 'Currently Breached');
END //

-- 4. Get Monthly Ticket Report
DROP PROCEDURE IF EXISTS get_monthly_ticket_report //
CREATE PROCEDURE get_monthly_ticket_report(IN p_year_month VARCHAR(7))
BEGIN
    IF p_year_month IS NULL OR p_year_month = '' THEN
        SELECT * FROM monthly_ticket_summary_view;
    ELSE
        SELECT * FROM monthly_ticket_summary_view WHERE ticket_month = p_year_month;
    END IF;
END //

DELIMITER ;
