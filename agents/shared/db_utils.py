"""
Database utilities for agents
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """Get database connection context manager"""
    conn = None
    try:
        conn = psycopg2.connect(
            os.getenv("DATABASE_URL", "postgresql://postgres:dev_password@localhost:5432/agentx")
        )
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def update_task_status(task_id: str, status: str, output: dict = None, error: str = None):
    """Update task status in database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            UPDATE tasks 
            SET status = %s, 
                output = %s, 
                error = %s,
                completed_at = CASE WHEN %s IN ('completed', 'failed') THEN NOW() ELSE completed_at END,
                started_at = CASE WHEN started_at IS NULL THEN NOW() ELSE started_at END
            WHERE id = %s
        """
        
        cursor.execute(query, (status, psycopg2.extras.Json(output or {}), error, status, task_id))
        logger.info(f"Updated task {task_id} to status: {status}")


def save_conversation_message(agent_id: str, task_id: str, role: str, content: str, metadata: dict = None):
    """Save a conversation message to database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            INSERT INTO conversations (agent_id, task_id, role, content, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (agent_id, task_id, role, content, psycopg2.extras.Json(metadata or {})))


def get_agent_by_type(agent_type: str) -> dict:
    """Get agent by type"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM agents WHERE type = %s", (agent_type,))
        return cursor.fetchone()
