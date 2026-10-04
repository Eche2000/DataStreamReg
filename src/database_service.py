import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg
except ImportError:
    psycopg = None


def _require_driver():
    if psycopg is None:
        raise ImportError("psycopg is not installed. Run: python3 -m pip install -r requirements.txt")


def connect_db():
    """Connect to PostgreSQL using DATABASE_URL from .env or the environment."""
    _require_driver()
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and add your Neon PostgreSQL connection string."
        )
    return psycopg.connect(url)


def create_table(conn=None, table_name="predictive_maintenance_robot_data"):
    """Create the predictive maintenance robot_data table if it does not already exist."""
    owns = conn is None
    if owns:
        conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    time TEXT,
                    trait TEXT,
                    "Axis #1" DOUBLE PRECISION,
                    "Axis #2" DOUBLE PRECISION,
                    "Axis #3" DOUBLE PRECISION,
                    "Axis #4" DOUBLE PRECISION,
                    "Axis #5" DOUBLE PRECISION,
                    "Axis #6" DOUBLE PRECISION,
                    "Axis #7" DOUBLE PRECISION,
                    "Axis #8" DOUBLE PRECISION,
                    "Axis #9" DOUBLE PRECISION,
                    "Axis #10" DOUBLE PRECISION,
                    "Axis #11" DOUBLE PRECISION,
                    "Axis #12" DOUBLE PRECISION,
                    "Axis #13" DOUBLE PRECISION,
                    "Axis #14" DOUBLE PRECISION
                )
            ''')
        conn.commit()
    finally:
        if owns:
            conn.close()


def insert_record(record_or_trait, *args, conn=None, table_name="predictive_maintenance_robot_data"):
    """Insert one pandas Series/dict or support the original positional workshop call."""
    owns = conn is None
    if owns:
        conn = connect_db()
    try:
        cols = ["time", "trait"] + [f"Axis #{i}" for i in range(1, 15)]

        if hasattr(record_or_trait, "to_dict"):
            record = record_or_trait.to_dict()
            values = [record.get(c) for c in cols]
        elif isinstance(record_or_trait, dict):
            values = [record_or_trait.get(c) for c in cols]
        else:
            # Original workshop signature:
            # insert_record(trait, axis1, ..., axis8, time)
            legacy = [record_or_trait, *args]
            if len(legacy) != 10:
                raise TypeError(
                    "insert_record expects a record/dict/Series or the legacy signature "
                    "(trait, axis1..axis8, time)."
                )
            trait, *axis_values, timestamp = legacy
            values = [timestamp, trait, *axis_values, *([None] * 6)]

        quoted_cols = [c if c in ("time", "trait") else f'"{c}"' for c in cols]
        placeholders = ", ".join(["%s"] * len(cols))
        with conn.cursor() as cur:
            cur.execute(
                f'INSERT INTO {table_name} ({", ".join(quoted_cols)}) VALUES ({placeholders})',
                values,
            )
        conn.commit()
    finally:
        if owns:
            conn.close()


def get_records(limit: Optional[int] = None, conn=None, table_name="predictive_maintenance_robot_data"):
    """Return stored robot records as a pandas DataFrame."""
    import pandas as pd

    owns = conn is None
    if owns:
        conn = connect_db()
    try:
        query = f'SELECT * FROM {table_name}'
        if limit is not None:
            query += f' LIMIT {int(limit)}'
        return pd.read_sql_query(query, conn)
    finally:
        if owns:
            conn.close()


def insert_dataframe(df, conn=None, table_name="predictive_maintenance_robot_data"):
    """Bulk insert a robot DataFrame into PostgreSQL and return inserted row count."""
    owns = conn is None
    if owns:
        conn = connect_db()
    try:
        cols = ["time", "trait"] + [f"Axis #{i}" for i in range(1, 15)]
        rows = []
        for _, record in df.iterrows():
            values = [record.get("Time", record.get("time")), record.get("Trait", record.get("trait"))]
            values.extend(record.get(f"Axis #{i}") for i in range(1, 15))
            rows.append(tuple(values))
        quoted_cols = [c if c in ("time", "trait") else f'"{c}"' for c in cols]
        placeholders = ", ".join(["%s"] * len(cols))
        query = f'INSERT INTO {table_name} ({", ".join(quoted_cols)}) VALUES ({placeholders})'
        with conn.cursor() as cur:
            cur.executemany(query, rows)
        conn.commit()
        return len(rows)
    finally:
        if owns:
            conn.close()
