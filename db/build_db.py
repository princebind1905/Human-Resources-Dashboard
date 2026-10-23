"""
Builds a SQLite database (db/hr.db) from data/employees.csv.

Run this once before starting the Streamlit app:
    python db/build_db.py
"""
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "employees.csv"
DB_PATH = ROOT / "db" / "hr.db"


def build():
    df = pd.read_csv(
        CSV_PATH,
        parse_dates=["Birthdate", "Hiredate", "Termdate"],
    )

    # Normalize date columns to plain ISO strings (SQLite has no native DATE type)
    for col in ["Birthdate", "Hiredate", "Termdate"]:
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("employees", conn, if_exists="replace", index=False)

    # Helpful indexes for the filters/joins the dashboard runs repeatedly
    cur = conn.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS idx_department ON employees(Department)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_state ON employees(State)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON employees(Status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gender ON employees(Gender)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_education ON employees(\"Education Level\")")
    conn.commit()

    n = cur.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    print(f"Built {DB_PATH} with {n:,} rows in table 'employees'.")
    conn.close()


if __name__ == "__main__":
    build()
