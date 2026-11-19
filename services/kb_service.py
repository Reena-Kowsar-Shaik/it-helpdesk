from typing import List, Dict, Optional
from database.connection import db_manager

class KBService:
    @staticmethod
    def get_articles(category: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
        """Fetches KB articles with optional category and keyword search."""
        sql = """
            SELECT kb.*, u.full_name AS author_name 
            FROM knowledge_base kb
            LEFT JOIN users u ON kb.created_by = u.user_id
            WHERE 1=1
        """
        params = {}
        if category and category != "All Categories":
            sql += " AND kb.category = :cat"
            params["cat"] = category
        if search:
            sql += " AND (LOWER(kb.title) LIKE :q OR LOWER(kb.content) LIKE :q OR LOWER(kb.tags) LIKE :q)"
            params["q"] = f"%{search.lower()}%"

        sql += " ORDER BY kb.helpful_count DESC, kb.view_count DESC;"
        return db_manager.execute_query(sql, params)

    @staticmethod
    def create_article(title: str, category: str, content: str, tags: str, user_id: int):
        """Creates a new KB self-service article."""
        sql = """
            INSERT INTO knowledge_base (title, category, content, tags, created_by)
            VALUES (:title, :category, :content, :tags, :created_by)
        """
        return db_manager.execute_non_query(sql, {
            "title": title.strip(), "category": category,
            "content": content.strip(), "tags": tags.strip(),
            "created_by": user_id
        })

    @staticmethod
    def mark_helpful(article_id: int):
        """Increments helpful upvote counter."""
        sql = "UPDATE knowledge_base SET helpful_count = helpful_count + 1 WHERE article_id = :id"
        db_manager.execute_non_query(sql, {"id": article_id})

    @staticmethod
    def get_canned_responses(category: Optional[str] = None) -> List[Dict]:
        """Fetches canned response templates."""
        sql = "SELECT * FROM canned_responses WHERE 1=1"
        params = {}
        if category:
            sql += " AND category = :cat"
            params["cat"] = category
        return db_manager.execute_query(sql, params)
