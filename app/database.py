"""
database.py
Handles SQLAlchemy engine creation and pandas query execution.
"""

import os
import pandas as pd
from sqlalchemy import create_engine , text
from dotenv import load_dotenv

load_dotenv()

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = (
            f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def run_query(sql: str, params: dict = None) -> pd.DataFrame:
    """Execute a SQL string with named params and return a DataFrame."""
    import decimal
    with get_engine().connect() as conn:
        stmt = text(sql)
        result = conn.execute(stmt, params or {})
        df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
        # Convert Decimal columns to float so Plotly/pandas arithmetic works
        for col in df.columns:
            if df[col].dtype == object and len(df) > 0:
                if isinstance(df[col].dropna().iloc[0] if not df[col].dropna().empty else None, decimal.Decimal):
                    df[col] = df[col].astype(float)
        return df
