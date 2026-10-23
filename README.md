# HR Analytics Dashboard — Python / SQL / SQLite / Streamlit

A rebuild of the original Tableau "Human Resources Dashboard" using only Python,
SQL, CSV, and Streamlit — no Tableau or Power BI required.

## Stack
- **CSV** (`data/employees.csv`) — the source data: 8,950 employee records
- **SQLite** (`db/hr.db`) — built from the CSV, queried with real SQL (see `sql/queries.sql`)
- **Streamlit** (`app.py`) — the web UI, with Plotly charts and sidebar filters
- Every chart and table in the app is backed by a parameterized SQL query, not
  pandas post-processing — filters (Department, State, Gender, Education) are
  pushed down into the `WHERE` clause.

## Setup

```bash
# 1. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the SQLite database from the CSV (run once, or after updating the CSV)
python db/build_db.py

# 4. Launch the dashboard
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Project structure

```
.
├── app.py                # Streamlit app — 4 tabs: Overview, Demographics, Income, Records
├── requirements.txt
├── data/
│   └── employees.csv     # source data (8,950 rows)
├── db/
│   ├── build_db.py       # CSV -> SQLite loader
│   └── hr.db             # generated (git-ignore this if versioning)
└── sql/
    └── queries.sql        # every query the app runs, documented and runnable standalone
```

## Data dictionary

| Column | Description |
|---|---|
| Employee_ID | Unique employee identifier |
| Full Name / First Name / Last Name | Employee name |
| Gender | Male / Female |
| Age / Age Group | Current age, bucketed into <25, 25-34, 35-44, 45-54, 55+ |
| State / City | Work location |
| Location Type | HQ if State = New York, else Branch |
| Department | Operations, Sales, IT, Customer Service, Marketing, Finance, HR |
| Job Title | Employee role |
| Education Level | High School, Bachelor, Master, PhD |
| Hiredate / Termdate | Employment start/end (Termdate blank if still active) |
| Status | Active or Terminated (derived from Termdate) |
| Tenure (Years) | Years employed, to Termdate or today |
| Salary | Annual salary, USD |
| Performance Rating | Excellent, Good, Satisfactory, Needs Improvement |

## Rebuilding the database after editing the CSV

```bash
python db/build_db.py
```

This drops and recreates the `employees` table and its indexes, so it's safe to
re-run any time the CSV changes.

## Extending it

- Swap `db/hr.db` for a Postgres/MySQL connection by changing `get_connection()`
  in `app.py` (swap `sqlite3.connect` for `sqlalchemy.create_engine`).
- Add `st.plotly_chart(..., on_select="rerun")` on the department/state charts
  for native click-to-filter instead of the sidebar dropdowns.
- Deploy for free on [Streamlit Community Cloud](https://streamlit.io/cloud) —
  push this folder to a GitHub repo and point it at `app.py`.
