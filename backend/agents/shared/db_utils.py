"""
Database utilities for agents
"""

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)

# Singleton connection pool instance
_pool = None
_pool_lock = threading.Lock()
_db_unavailable = False  # Flag to track if DB is unavailable (skip operations if True)
_db_unavailable_lock = threading.Lock()


def _log_pool_statistics():
    """Log connection pool statistics for monitoring"""
    global _pool
    if _pool is None:
        return
    
    try:
        # ThreadedConnectionPool doesn't expose statistics directly,
        # but we can log that the pool exists and is being used
        logger.debug("[DB_POOL] Pool statistics: pool_active=True, minconn=2, maxconn=10")
    except Exception as e:
        logger.debug(f"[DB_POOL] Could not retrieve pool statistics: {e}")


def _get_connection_pool():
    """Get or create the database connection pool (singleton pattern)"""
    global _pool
    
    if _pool is None:
        with _pool_lock:
            # Double-check locking pattern
            if _pool is None:
                database_url = os.getenv("DATABASE_URL", "postgresql://postgres:dev_password@localhost:5432/agentx")
                
                # Parse connection parameters for pool
                try:
                    # Extract connection parameters from URL
                    from urllib.parse import urlparse
                    parsed = urlparse(database_url)
                    
                    pool_config = {
                        'minconn': 0,  # Changed from 2 to 0 - don't create connections immediately (lazy initialization)
                        'maxconn': 10,
                        'host': parsed.hostname or 'localhost',
                        'port': parsed.port or 5432,
                        'database': parsed.path.lstrip('/') or 'agentx',
                        'user': parsed.username or 'postgres',
                        'password': parsed.password or 'dev_password',
                    }
                    
                    # Add SSL mode if specified
                    if 'sslmode' in parsed.query:
                        pool_config['sslmode'] = parsed.query.split('sslmode=')[1].split('&')[0]
                    else:
                        # Default to disable SSL for local connections to avoid GSSAPI issues
                        pool_config['sslmode'] = 'disable'
                    
                    logger.info(f"[DB_POOL] Initializing connection pool: minconn=0 (lazy), maxconn=10, host={pool_config['host']}, connect_timeout=5s")
                    
                    _pool = pool.ThreadedConnectionPool(
                        minconn=pool_config['minconn'],
                        maxconn=pool_config['maxconn'],
                        host=pool_config['host'],
                        port=pool_config['port'],
                        database=pool_config['database'],
                        user=pool_config['user'],
                        password=pool_config['password'],
                        connect_timeout=5,  # Fail fast in office networks
                        **({k: v for k, v in pool_config.items() if k in ['sslmode']})
                    )
                    # Note: With minconn=0, connections are created lazily on first use, not during pool initialization
                    # This prevents blocking during pool creation if database is unavailable
                    
                    logger.info("[DB_POOL] Connection pool initialized successfully")
                    _log_pool_statistics()
                    
                except Exception as e:
                    logger.error(f"[DB_POOL] Failed to create connection pool: {e}")
                    raise
    
    return _pool


def _check_connection_health(conn):
    """Check if a connection is healthy"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        return False


def _getconn_with_timeout(pool_instance, timeout_seconds=6):
    """Get connection from pool with timeout to prevent blocking"""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(pool_instance.getconn)
    try:
        conn = future.result(timeout=timeout_seconds)
        executor.shutdown(wait=False)
        return conn
    except FutureTimeoutError:
        executor.shutdown(wait=False)
        raise TimeoutError(f"Connection acquisition timed out after {timeout_seconds}s")
    except Exception as e:
        executor.shutdown(wait=False)
        raise


def is_db_available() -> bool:
    """Check if database is available (for optional operations like cache)"""
    global _db_unavailable
    with _db_unavailable_lock:
        return not _db_unavailable


@contextmanager
def get_db_connection():
    """Get database connection from pool (context manager) with timeout protection"""
    global _db_unavailable
    
    # Fast path: if DB is known to be unavailable, fail immediately
    if _db_unavailable:
        raise psycopg2.OperationalError("Database is unavailable (previous connection attempts failed)")
    
    try:
        pool_instance = _get_connection_pool()
    except Exception as e:
        # If pool creation fails, mark DB as unavailable and raise
        with _db_unavailable_lock:
            _db_unavailable = True
        logger.error(f"[DB_POOL] Failed to get connection pool: {e}")
        raise
    
    conn = None
    retries = 0
    max_retries = 1  # Reduced from 3 to 1 - fail fast if DB is unavailable
    connection_timeout = 6  # 6 seconds max for connection acquisition (slightly more than connect_timeout=5)
    
    while retries < max_retries:
        try:
            conn_start = time.monotonic()
            # Use timeout wrapper to prevent getconn() from blocking for 2+ minutes
            try:
                conn = _getconn_with_timeout(pool_instance, timeout_seconds=connection_timeout)
            except TimeoutError as e:
                logger.warning(f"[DB_POOL] Connection acquisition timeout: {e}")
                raise psycopg2.OperationalError(f"Connection timeout: {e}")
            
            conn_time = time.monotonic() - conn_start
            
            if conn_time > 1.0:
                logger.warning(f"[DB_POOL] Slow connection acquisition: {conn_time:.2f}s")
            elif conn_time > 0.1:
                logger.debug(f"[DB_POOL] Connection acquired in {conn_time:.3f}s")
            
            # Health check the connection
            if not _check_connection_health(conn):
                logger.warning("[DB_POOL] Connection failed health check, getting new one")
                pool_instance.putconn(conn, close=True)
                conn = None
                retries += 1
                continue
            
            try:
                yield conn
                conn.commit()
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"[DB_POOL] Database error: {e}")
                raise
            finally:
                if conn:
                    pool_instance.putconn(conn)
                    conn = None
            break
            
        except (pool.PoolError, psycopg2.OperationalError, psycopg2.InterfaceError, TimeoutError) as e:
            # Fail fast on connection errors - don't retry multiple times
            logger.warning(f"[DB_POOL] Connection error (retry {retries + 1}/{max_retries}): {e}")
            if conn:
                try:
                    pool_instance.putconn(conn, close=True)
                except Exception:
                    pass
                conn = None
            retries += 1
            if retries >= max_retries:
                # Mark DB as unavailable after max retries
                with _db_unavailable_lock:
                    _db_unavailable = True
                # Re-raise to allow caller to handle (e.g., cache operations can skip DB)
                raise
            time.sleep(0.1)  # Short backoff before single retry
        
        except Exception as e:
            if conn:
                try:
                    pool_instance.putconn(conn, close=True)
                except Exception:
                    pass
            logger.error(f"[DB_POOL] Unexpected error: {e}")
            raise


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
