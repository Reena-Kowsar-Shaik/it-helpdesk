-- ==========================================================
-- IT Helpdesk & Ticket Management System - Triggers
-- Automatically maintain audit trail in ticket_history
-- ==========================================================

USE it_helpdesk_db;

DELIMITER //

-- 1. Trigger on Ticket Creation: Initialize audit entry
DROP TRIGGER IF EXISTS trg_after_ticket_insert //
CREATE TRIGGER trg_after_ticket_insert
AFTER INSERT ON tickets
FOR EACH ROW
BEGIN
    INSERT INTO ticket_history (
        ticket_id, 
        old_status, 
        new_status, 
        changed_by_user_id, 
        comment, 
        changed_at
    ) VALUES (
        NEW.ticket_id, 
        NULL, 
        NEW.status, 
        (SELECT user_id FROM employees WHERE employee_id = NEW.employee_id LIMIT 1), 
        CONCAT('Ticket #', NEW.ticket_number, ' created with priority ', NEW.priority), 
        NOW()
    );
END //

-- 2. Trigger on Ticket Status Update: Log status transition
DROP TRIGGER IF EXISTS trg_after_ticket_status_update //
CREATE TRIGGER trg_after_ticket_status_update
AFTER UPDATE ON tickets
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO ticket_history (
            ticket_id, 
            old_status, 
            new_status, 
            changed_by_user_id, 
            comment, 
            changed_at
        ) VALUES (
            NEW.ticket_id, 
            OLD.status, 
            NEW.status, 
            NULL, 
            CONCAT('Status transition: ', OLD.status, ' -> ', NEW.status), 
            NOW()
        );
    END IF;
END //

DELIMITER ;
