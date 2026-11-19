import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from services.auth_service import AuthService
from services.ticket_service import TicketService
from services.sla_service import SLAService
from services.analytics_service import AnalyticsService
from services.ai_service import AIAssistantService
from services.export_service import ExportService

class TestHelpdeskSystem(unittest.TestCase):
    def test_auth_login(self):
        user = AuthService.login("admin@enterprise.com", "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "IT Admin")

    def test_analytics_kpi(self):
        kpi = AnalyticsService.get_kpi_summary()
        self.assertGreater(kpi["total_tickets"], 0)
        self.assertIn("sla_compliance_pct", kpi)

    def test_agent_rankings(self):
        df = AnalyticsService.get_agent_rankings()
        self.assertFalse(df.empty)
        self.assertIn("agent_name", df.columns)
        self.assertIn("performance_rank", df.columns)

    def test_ticket_creation_and_lifecycle(self):
        res = TicketService.create_ticket(
            title="Unit Test Outage Incident",
            description="Testing automated ticket workflow and SLA tracking",
            category="Database & Cloud Infrastructure",
            priority="Critical",
            requester_id=1,
            auto_assign=True
        )
        self.assertTrue(res["success"])
        ticket_id = res["ticket_id"]

        # Check details
        t = TicketService.get_ticket_details(ticket_id)
        self.assertIsNotNone(t)
        self.assertEqual(t["priority"], "Critical")

        # Update status
        updated = TicketService.update_ticket_status(
            ticket_id=ticket_id,
            new_status="Resolved",
            user_id=1,
            resolution_notes="Resolved via unit test execution.",
            root_cause="Test mock failure"
        )
        self.assertTrue(updated)

    def test_ai_incident_analyzer(self):
        analysis = AIAssistantService.analyze_incident("Urgent outage: Production database connection timeout and crashing")
        self.assertEqual(analysis["recommended_priority"], "Critical")
        self.assertEqual(analysis["recommended_category"], "Database & Cloud Infrastructure")

    def test_export_generation(self):
        excel_bytes = ExportService.generate_excel_report()
        self.assertGreater(len(excel_bytes), 1000)

        pdf_bytes = ExportService.generate_pdf_report()
        self.assertGreater(len(pdf_bytes), 1000)

if __name__ == "__main__":
    unittest.main()
