# db.py
# -----------------------------
# Database connector with Connection Pooling
# -----------------------------

import os
import mysql.connector
from mysql.connector import pooling
from typing import Any, List, Tuple, Dict
from contextlib import contextmanager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "pantrywise"),
    "autocommit": False,
}

# Create connection pool (reuses connections instead of creating new ones)
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="pantrywise_pool",
        pool_size=5,  # Max 5 concurrent connections
        pool_reset_session=True,
        **DB_CONFIG
    )
except mysql.connector.Error as e:
    print(f"Warning: Could not create connection pool: {e}")
    connection_pool = None

@contextmanager
def get_connection():
    """Context manager for database connections from the pool."""
    conn = None
    try:
        if connection_pool:
            conn = connection_pool.get_connection()
        else:
            # Fallback to direct connection if pool unavailable
            conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn and conn.is_connected():
            conn.close()

def query_all(sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    """Run SELECT query and return all rows as list of dicts."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

def query_one(sql: str, params: Tuple[Any, ...] = ()) -> Dict[str, Any] | None:
    """Run SELECT query and return first row or None."""
    rows = query_all(sql, params)
    return rows[0] if rows else None

def execute(sql: str, params: Tuple[Any, ...] = ()) -> int:
    """Run INSERT/UPDATE/DELETE with commit. Returns lastrowid."""
    with get_connection() as conn:
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            last_id = cur.lastrowid if hasattr(cur, "lastrowid") else -1
            conn.commit()
            cur.close()
            return last_id
        except Exception as e:
            conn.rollback()
            raise e

def execute_many(sql: str, params_list: List[Tuple[Any, ...]]) -> int:
    """Execute same SQL with multiple param sets (batch insert)."""
    with get_connection() as conn:
        try:
            cur = conn.cursor()
            cur.executemany(sql, params_list)
            conn.commit()
            affected = cur.rowcount
            cur.close()
            return affected
        except Exception as e:
            conn.rollback()
            raise e
