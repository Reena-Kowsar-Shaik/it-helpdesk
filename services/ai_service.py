import re
import difflib
from typing import List, Dict
from database.connection import db_manager

class AIAssistantService:
    @staticmethod
    def analyze_incident(text: str) -> Dict:
        """
        Analyzes ticket text to predict priority, category, sentiment, and urgency.
        """
        text_lower = text.lower()

        # Priority Detection
        priority = "Medium"
        if any(w in text_lower for w in ["outage", "emergency", "production down", "urgent", "crashloop", "breach", "phishing", "firewall down", "swelling", "critical", "blocked all"]):
            priority = "Critical"
        elif any(w in text_lower for w in ["major", "cannot access", "disconnected", "failing", "broken", "severe", "deadline", "pitch"]):
            priority = "High"
        elif any(w in text_lower for w in ["request", "minor", "documentation", "inquiry", "how to", "cable", "license"]):
            priority = "Low"

        # Category Detection
        category = "General IT Support"
        if any(w in text_lower for w in ["macbook", "laptop", "screen", "keyboard", "monitor", "battery", "hardware", "dell", "flicker"]):
            category = "Hardware & Workstations"
        elif any(w in text_lower for w in ["vpn", "wifi", "wi-fi", "network", "internet", "dns", "gateway", "router"]):
            category = "Network & VPN Connectivity"
        elif any(w in text_lower for w in ["login", "sso", "okta", "password", "access denied", "403", "permission", "mfa"]):
            category = "Identity & Access Management"
        elif any(w in text_lower for w in ["database", "postgres", "mysql", "aws", "kubernetes", "s3", "cloud", "server", "docker"]):
            category = "Database & Cloud Infrastructure"
        elif any(w in text_lower for w in ["excel", "jira", "license", "software", "install", "app crash", "tableau"]):
            category = "Software & Licensing"
        elif any(w in text_lower for w in ["phishing", "malware", "virus", "security", "defender", "trojan", "quarantine"]):
            category = "Security & Incident Response"
        elif any(w in text_lower for w in ["outlook", "email", "teams", "slack", "zoom", "mailbox"]):
            category = "Email & Communication Systems"
        elif any(w in text_lower for w in ["printer", "toner", "paper jam", "scanner"]):
            category = "Printer & Peripherals"

        # Sentiment & Urgency
        sentiment = "Neutral"
        urgency = "Normal"
        if any(w in text_lower for w in ["angry", "unacceptable", "furious", "terrible", "again", "frustrated", "still broken"]):
            sentiment = "Negative / Frustrated"
            urgency = "Escalated"
        elif priority == "Critical":
            urgency = "Immediate Attention Needed"

        return {
            "recommended_priority": priority,
            "recommended_category": category,
            "sentiment": sentiment,
            "urgency": urgency
        }

    @staticmethod
    def find_similar_tickets(query_text: str, limit: int = 5) -> List[Dict]:
        """
        Searches historical resolved/closed tickets to detect potential duplicates or known fixes.
        """
        sql = """
            SELECT ticket_id, ticket_number, title, category, priority, status, 
                   resolution_notes, root_cause
            FROM tickets
            ORDER BY ticket_id DESC
        """
        tickets = db_manager.execute_query(sql)
        query_words = set(re.findall(r'\w+', query_text.lower()))

        scored = []
        for t in tickets:
            ticket_words = set(re.findall(r'\w+', (t["title"] + " " + (t.get("resolution_notes") or "")).lower()))
            if not ticket_words or not query_words:
                continue
            
            # Jaccard + Sequence Matcher similarity
            intersection = query_words.intersection(ticket_words)
            union = query_words.union(ticket_words)
            jaccard = len(intersection) / len(union) if union else 0
            seq_sim = difflib.SequenceMatcher(None, query_text.lower(), t["title"].lower()).ratio()
            score = (jaccard * 0.4) + (seq_sim * 0.6)

            if score > 0.15:
                t["similarity_score"] = round(score * 100, 1)
                scored.append(t)

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:limit]

    @staticmethod
    def recommend_knowledge_articles(query_text: str, limit: int = 3) -> List[Dict]:
        """Recommends relevant KB articles for self-service or agent resolution."""
        sql = "SELECT article_id, title, category, content, tags, helpful_count FROM knowledge_base;"
        articles = db_manager.execute_query(sql)
        query_words = set(re.findall(r'\w+', query_text.lower()))

        scored = []
        for a in articles:
            searchable = (a["title"] + " " + a["content"] + " " + (a.get("tags") or "")).lower()
            art_words = set(re.findall(r'\w+', searchable))
            overlap = len(query_words.intersection(art_words))
            if overlap > 0:
                a["match_score"] = overlap
                scored.append(a)

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:limit]
