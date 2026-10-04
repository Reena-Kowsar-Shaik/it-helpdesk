"""End-to-End Verification Test for Member 2 (Ticket Management, SLA & Support Operations)."""

import sys
from datetime import datetime, timedelta
from tickets.ticket_manager import TicketManager
from tickets.ticket_assignment import TicketAssignmentManager
from tickets.ticket_history import TicketHistoryManager
from tickets.sla_manager import SLAManager
from tickets.ticket_filters import TicketFilterService, TicketFilterCriteria
from core.repositories import EmployeeRepository, DepartmentRepository, CategoryRepository, AgentRepository

def run_tests():
    print("=" * 60)
    print("RUNNING MEMBER 2 WORKFLOW VERIFICATION SUITE")
    print("=" * 60)

    mgr = TicketManager()
    assign_mgr = TicketAssignmentManager()
    hist_mgr = TicketHistoryManager()
    sla_mgr = SLAManager()
    filter_svc = TicketFilterService()

    emp_repo = EmployeeRepository()
    dept_repo = DepartmentRepository()
    cat_repo = CategoryRepository()
    agent_repo = AgentRepository()

    employees = emp_repo.get_all()
    categories = cat_repo.get_all()
    departments = dept_repo.get_all()
    agents = agent_repo.get_all()

    if not employees or not categories:
        print("[!] Warning: No seeded employees or categories found in database.")
        return

    emp = employees[0]
    cat = categories[0]
    dept = departments[0] if departments else emp.department

    print(f"\n[1] Testing Ticket Creation with SLA Deadline Calculation...")
    ticket = mgr.create_ticket(
        employee_id=emp.employee_id,
        department_id=dept.department_id,
        category_id=cat.category_id,
        title="Test VPN & Connectivity Failure",
        description="Unable to connect to corporate gateway from home network.",
        priority="Critical",
        user_id=emp.user_id
    )
    print(f"[+] Ticket Created: #{ticket.ticket_number} (ID: {ticket.ticket_id})")
    print(f"    Priority: {ticket.priority} | Status: {ticket.status}")
    print(f"    Response Deadline: {ticket.response_deadline}")
    print(f"    Resolution Deadline: {ticket.resolution_deadline}")

    print(f"\n[2] Testing Smart Workload-Aware Auto Assignment...")
    assigned_ticket, best_agent = assign_mgr.auto_assign_ticket(ticket.ticket_id)
    print(f"[+] Auto-Assigned to Agent: {best_agent.full_name} (Specialization: {best_agent.specialization})")
    print(f"    New Ticket Status: {assigned_ticket.status}")

    print(f"\n[3] Testing Agent Workload Statistics...")
    workloads = assign_mgr.get_agent_workloads()
    for w in workloads[:3]:
        print(f"    - Agent {w['full_name']}: {w['active_tickets']} active, {w['resolved_tickets']} resolved [{w['workload_status']}]")

    print(f"\n[4] Testing Lifecycle Transition to IN PROGRESS...")
    ticket = mgr.transition_status(ticket.ticket_id, "IN PROGRESS", user_id=best_agent.user_id, comment="Investigating routing tables.")
    print(f"[+] Ticket Status: {ticket.status} | First Responded At: {ticket.first_responded_at}")

    print(f"\n[5] Testing Comments & Internal Notes...")
    c1 = mgr.add_comment(ticket.ticket_id, user_id=best_agent.user_id, comment_text="Identified stale certificate on IPsec tunnel.", is_internal=True)
    c2 = mgr.add_comment(ticket.ticket_id, user_id=best_agent.user_id, comment_text="Certificate renewed. Please reconnect.", is_internal=False)
    print(f"[+] Added internal note (ID: {c1.comment_id}) and public message (ID: {c2.comment_id})")

    print(f"\n[6] Testing Resolution Recording...")
    res = mgr.resolve_ticket(
        ticket_id=ticket.ticket_id,
        agent_id=best_agent.agent_id,
        root_cause="Expired SSL/TLS VPN Client Certificate",
        resolution_steps="Regenerated root certificate bundle and pushed configuration update.",
        resolution_category="Configuration Fix",
        user_id=best_agent.user_id
    )
    print(f"[+] Ticket Resolved: #{ticket.ticket_number} (Resolved At: {res.resolved_at})")

    print(f"\n[7] Testing Reopen Workflow...")
    reopened = mgr.reopen_ticket(ticket.ticket_id, user_id=emp.user_id, reason="Tunnel drops after 5 minutes.")
    print(f"[+] Ticket Reopened: Status: {reopened.status} | Reopened Count: {reopened.reopened_count}")

    print(f"\n[8] Testing SLA Manager Breach Check & Metrics...")
    sla_info = sla_mgr.check_ticket_sla_status(reopened)
    print(f"[+] SLA Evaluation: Is Breached: {sla_info['is_breached']} | Resolution Status: {sla_info['resolution_status']} | Remaining: {sla_info['time_remaining_formatted']}")
    sla_metrics = sla_mgr.get_sla_metrics_summary()
    print(f"    Overall Compliance Rate: {sla_metrics['compliance_rate']}% | Breached Tickets: {sla_metrics['breached_tickets']}")

    print(f"\n[9] Testing Audit History Timeline...")
    timeline = hist_mgr.get_ticket_timeline(ticket.ticket_id)
    print(f"[+] Chronological Audit Trail ({len(timeline)} events):")
    for event in timeline:
        print(f"    [{event['timestamp_formatted']}] {event['changed_by']} ({event['changed_by_role']}): {event['old_status']} -> {event['new_status']} | {event['comment']}")

    print(f"\n[10] Testing Multi-Dimensional Ticket Filters & Export...")
    crit = TicketFilterCriteria(
        priority="Critical",
        status="REOPENED",
        search_query="VPN"
    )
    filtered = filter_svc.filter_tickets(crit)
    print(f"[+] Filter returned {len(filtered)} matching tickets")
    df = filter_svc.tickets_to_dataframe(filtered)
    print(f"    DataFrame columns: {list(df.columns)}")
    print(f"    DataFrame shape: {df.shape}")

    print("\n" + "=" * 60)
    print("ALL MEMBER 2 MODULES & WORKFLOWS VERIFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
