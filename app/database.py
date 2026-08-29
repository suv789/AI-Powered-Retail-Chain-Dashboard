"""
database.py
Handles SQLAlchemy engine creation and pandas query execution.
"""

import os
import decimal
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        try:
            import streamlit as st
            db_user = st.secrets["postgres"]["username"]
            db_password = st.secrets["postgres"]["password"]
            db_host = st.secrets["postgres"]["host"]
            db_port = st.secrets["postgres"]["port"]
            db_name = st.secrets["postgres"]["database"]
        except Exception:
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME")

        url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
        _engine = create_engine(
            url,
            connect_args={"options": "-csearch_path=public"},
            pool_pre_ping=True
        )
    return _engine


def run_query(sql: str, params: dict = None) -> pd.DataFrame:
    """Execute a SQL string with named params and return a DataFrame."""
    with get_engine().connect() as conn:
        stmt = text(sql)
        result = conn.execute(stmt, params or {})
        df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
        # Convert Decimal columns to float so Plotly/pandas arithmetic works
        for col in df.columns:
            if df[col].dtype == object and len(df) > 0:
                first_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(first_val, decimal.Decimal):
                    df[col] = df[col].astype(float)
        return df