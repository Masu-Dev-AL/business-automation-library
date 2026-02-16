import os
import streamlit as st
import pandas as pd
import psycopg
from dotenv import load_dotenv


@st.cache_resource
def get_connection():
    """Return a cached psycopg connection to PostgreSQL."""
    env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
    load_dotenv(env_path)

    try:
        conn = psycopg.connect(
            host=os.getenv("DB_HOST", "172.17.0.1"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "ecommerce_inventory"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            autocommit=True,
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


@st.cache_data(ttl=300)
def run_query(sql, params=None):
    """Execute SQL and return results as a DataFrame. Cached for 5 minutes."""
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()
