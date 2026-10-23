"""
HR Analytics Dashboard — Streamlit + SQLite edition
Run:
    python db/build_db.py   # once, to build db/hr.db from data/employees.csv
    streamlit run app.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "db" / "hr.db"

# Streamlit Community Cloud only installs requirements.txt and runs this file —
# it never runs db/build_db.py. hr.db is gitignored, so build it on first run
# if it isn't there yet (local dev already has it from running build_db.py).
if not DB_PATH.exists():
    from db.build_db import build
    build()

TEAL = "#17B897"
MAGENTA = "#E0447A"
AMBER = "#F2A65A"
BLUE = "#5B8DEF"
BG = "#0F1319"
PANEL = "#171C24"
TEXT = "#F2F4F7"
SUB = "#8A93A3"

# ----------------------------------------------------------------------
# Page config + theme
# ----------------------------------------------------------------------
st.set_page_config(page_title="HR Analytics Dashboard", layout="wide", page_icon="👥")

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BG}; color: {TEXT}; }}
    section[data-testid="stSidebar"] {{ background-color: {PANEL}; }}
    div[data-testid="stMetric"] {{
        background-color: {PANEL}; border: 1px solid #262E3A; border-radius: 14px;
        padding: 18px 16px 14px;
        min-height: 150px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
    }}
    div[data-testid="stMetricLabel"] {{ color: {SUB}; margin-top: auto; }}
    div[data-testid="stMetricValue"] {{
        font-size: clamp(2.7rem, 3vw, 4rem);
        line-height: 1.1;
        letter-spacing: -0.06em;
    }}
    .block-container {{ padding-top: 1.4rem; }}
    h1, h2, h3 {{ color: {TEXT}; }}
    .stTabs [data-baseweb="tab"] {{ font-weight: 600; }}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor=PANEL,
    plot_bgcolor=PANEL,
    font_color=TEXT,
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


# ----------------------------------------------------------------------
# Data access layer — every chart/table below is backed by a real SQL query
# ----------------------------------------------------------------------
@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        st.error(
            "Database not found. Run `python db/build_db.py` once from the "
            "project folder before starting the app."
        )
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_connection(), params=params)


def build_filter_clause(dept, state, gender, edu):
    clauses, params = [], []
    if dept != "All":
        clauses.append("Department = ?")
        params.append(dept)
    if state != "All":
        clauses.append("State = ?")
        params.append(state)
    if gender != "All":
        clauses.append("Gender = ?")
        params.append(gender)
    if edu != "All":
        clauses.append('"Education Level" = ?')
        params.append(edu)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, tuple(params)


# ----------------------------------------------------------------------
# Sidebar filters (drive every SQL query below)
# ----------------------------------------------------------------------
st.sidebar.markdown("## 👥 HR Dashboard")
st.sidebar.caption("SQLite + Streamlit edition · 8,950 employees")

departments = ["All"] + run_query("SELECT DISTINCT Department FROM employees ORDER BY 1")["Department"].tolist()
states = ["All"] + run_query("SELECT DISTINCT State FROM employees ORDER BY 1")["State"].tolist()
genders = ["All"] + run_query("SELECT DISTINCT Gender FROM employees ORDER BY 1")["Gender"].tolist()
edus = ["All"] + run_query('SELECT DISTINCT "Education Level" FROM employees ORDER BY 1')["Education Level"].tolist()

f_dept = st.sidebar.selectbox("Department", departments)
f_state = st.sidebar.selectbox("State", states)
f_gender = st.sidebar.selectbox("Gender", genders)
f_edu = st.sidebar.selectbox("Education Level", edus)

if st.sidebar.button("Reset filters"):
    f_dept, f_state, f_gender, f_edu = "All", "All", "All", "All"

WHERE, PARAMS = build_filter_clause(f_dept, f_state, f_gender, f_edu)

st.title("Human Resources Dashboard")
st.caption("Python · SQL · SQLite · Streamlit — Build by Prince Bind")

tab_overview, tab_demo, tab_income, tab_records = st.tabs(
    ["📊 Overview", "🧑‍🤝‍🧑 Demographics", "💰 Income", "📋 Employee Records"]
)

# ----------------------------------------------------------------------
# TAB 1 — Overview
# ----------------------------------------------------------------------
with tab_overview:
    kpi_sql = f"""
        SELECT
            COUNT(*) AS total_ever,
            SUM(CASE WHEN Status='Active' THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN Status='Terminated' THEN 1 ELSE 0 END) AS terminated,
            ROUND(AVG("Tenure (Years)"), 1) AS avg_tenure
        FROM employees {WHERE}
    """
    kpi = run_query(kpi_sql, PARAMS).iloc[0]
    attrition = round(100 * kpi["terminated"] / kpi["total_ever"], 1) if kpi["total_ever"] else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Active Employees", f"{int(kpi['active']):,}", f"Attrition {attrition}%")
    c2.metric("Total Hired (Ever)", f"{int(kpi['total_ever']):,}")
    c3.metric("Terminated", f"{int(kpi['terminated']):,}", f"Avg tenure {kpi['avg_tenure']} yrs", delta_color="inverse")

    col_a, col_b = st.columns([1.2, 0.8])

    with col_a:
        st.subheader("Hiring vs Termination Trend")
        hires = run_query(
            f"SELECT strftime('%Y', Hiredate) AS yr, COUNT(*) AS hires FROM employees {WHERE} GROUP BY yr ORDER BY yr",
            PARAMS,
        )
        term_where = (WHERE + " AND Termdate IS NOT NULL") if WHERE else "WHERE Termdate IS NOT NULL"
        terms = run_query(
            f"SELECT strftime('%Y', Termdate) AS yr, COUNT(*) AS terminations FROM employees {term_where} GROUP BY yr ORDER BY yr",
            PARAMS,
        )
        trend = pd.merge(hires, terms, on="yr", how="outer").fillna(0).sort_values("yr")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["yr"], y=trend["hires"], name="Hired",
                                  line=dict(color=TEAL, width=3), fill="tozeroy", fillcolor="rgba(23,184,151,0.15)"))
        fig.add_trace(go.Scatter(x=trend["yr"], y=trend["terminations"], name="Terminated",
                                  line=dict(color=MAGENTA, width=3), fill="tozeroy", fillcolor="rgba(224,68,122,0.15)"))
        fig.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        st.subheader("Departments")
        dept_df = run_query(
            f"""SELECT Department,
                       SUM(CASE WHEN Status='Active' THEN 1 ELSE 0 END) AS Active,
                       SUM(CASE WHEN Status='Terminated' THEN 1 ELSE 0 END) AS Terminated
                FROM employees {WHERE}
                GROUP BY Department ORDER BY (Active+Terminated) DESC""",
            PARAMS,
        )
        fig = px.bar(dept_df, x=["Active", "Terminated"], y="Department", orientation="h",
                     color_discrete_map={"Active": TEAL, "Terminated": MAGENTA}, barmode="stack")
        fig.update_layout(**PLOTLY_LAYOUT, height=320, yaxis=dict(autorange="reversed"), legend_title=None)
        st.plotly_chart(fig, width='stretch')

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Employees by State")
        state_df = run_query(f"SELECT State, COUNT(*) AS Headcount FROM employees {WHERE} GROUP BY State ORDER BY Headcount DESC", PARAMS)
        fig = px.bar(state_df, x="Headcount", y="State", orientation="h", color_discrete_sequence=[TEAL])
        fig.update_layout(**PLOTLY_LAYOUT, height=320, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width='stretch')

    with col_d:
        st.subheader("HQ vs Branch")
        loc_df = run_query(f'SELECT "Location Type" AS loc, COUNT(*) AS n FROM employees {WHERE} GROUP BY loc', PARAMS)
        fig = px.pie(loc_df, names="loc", values="n", hole=0.65, color="loc",
                     color_discrete_map={"HQ": TEAL, "Branch": MAGENTA})
        fig.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig, width='stretch')

# ----------------------------------------------------------------------
# TAB 2 — Demographics
# ----------------------------------------------------------------------
with tab_demo:
    col_a, col_b, col_c = st.columns([0.8, 1.1, 1.1])

    with col_a:
        st.subheader("Gender Split")
        g_df = run_query(f"SELECT Gender, COUNT(*) AS n FROM employees {WHERE} GROUP BY Gender", PARAMS)
        fig = px.pie(g_df, names="Gender", values="n", hole=0.7, color="Gender",
                     color_discrete_map={"Male": TEAL, "Female": MAGENTA})
        fig.update_layout(**PLOTLY_LAYOUT, height=300)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        st.subheader("Education & Age")
        ea = run_query(
            f'SELECT "Age Group", "Education Level", COUNT(*) AS n FROM employees {WHERE} GROUP BY "Age Group", "Education Level"',
            PARAMS,
        )
        age_order = ["<25", "25-34", "35-44", "45-54", "55+"]
        edu_order = ["High School", "Bachelor", "Master", "PhD"]
        pivot = ea.pivot(index="Age Group", columns="Education Level", values="n").reindex(index=age_order, columns=edu_order).fillna(0)
        fig = px.imshow(pivot, text_auto=True, color_continuous_scale=[[0, PANEL], [1, TEAL]], aspect="auto")
        fig.update_layout(**PLOTLY_LAYOUT, height=300, coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')

    with col_c:
        st.subheader("Education & Performance")
        ep = run_query(
            f'SELECT "Performance Rating", "Education Level", COUNT(*) AS n FROM employees {WHERE} GROUP BY "Performance Rating", "Education Level"',
            PARAMS,
        )
        perf_order = ["Excellent", "Good", "Satisfactory", "Needs Improvement"]
        pivot2 = ep.pivot(index="Performance Rating", columns="Education Level", values="n").reindex(index=perf_order, columns=edu_order).fillna(0)
        fig = px.imshow(pivot2, text_auto=True, color_continuous_scale=[[0, PANEL], [1, TEAL]], aspect="auto")
        fig.update_layout(**PLOTLY_LAYOUT, height=300, coloraxis_showscale=False)
        st.plotly_chart(fig, width='stretch')

# ----------------------------------------------------------------------
# TAB 3 — Income
# ----------------------------------------------------------------------
with tab_income:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Average Salary — Education × Gender")
        sal = run_query(
            f'SELECT "Education Level", Gender, ROUND(AVG(Salary),0) AS avg_salary FROM employees {WHERE} GROUP BY "Education Level", Gender',
            PARAMS,
        )
        fig = px.bar(sal, x="Education Level", y="avg_salary", color="Gender", barmode="group",
                     category_orders={"Education Level": edu_order}, color_discrete_map={"Male": TEAL, "Female": MAGENTA})
        fig.update_layout(**PLOTLY_LAYOUT, height=380, yaxis_title="Avg Salary ($)")
        st.plotly_chart(fig, width='stretch')

        st.subheader("Pay-equity gap (extra)")
        gap = run_query(
            f"""SELECT "Education Level",
                       ROUND(AVG(CASE WHEN Gender='Male' THEN Salary END),0) AS male_avg,
                       ROUND(AVG(CASE WHEN Gender='Female' THEN Salary END),0) AS female_avg,
                       ROUND(100.0*(AVG(CASE WHEN Gender='Male' THEN Salary END)-AVG(CASE WHEN Gender='Female' THEN Salary END))
                             /AVG(CASE WHEN Gender='Male' THEN Salary END),1) AS pct_gap
                FROM employees {WHERE} GROUP BY "Education Level" """,
            PARAMS,
        )
        st.dataframe(gap, width='stretch', hide_index=True)

    with col_b:
        st.subheader("Age vs Salary by Role")
        scatter = run_query(
            f'SELECT "Job Title", Age, ROUND(AVG(Salary),0) AS avg_salary FROM employees {WHERE} GROUP BY "Job Title", Age',
            PARAMS,
        )
        fig = px.scatter(scatter, x="Age", y="avg_salary", hover_name="Job Title",
                          color_discrete_sequence=[TEAL], opacity=0.7)
        fig.update_traces(marker=dict(size=8))
        fig.update_layout(**PLOTLY_LAYOUT, height=520, yaxis_title="Salary ($)")
        st.plotly_chart(fig, width='stretch')

# ----------------------------------------------------------------------
# TAB 4 — Employee Records
# ----------------------------------------------------------------------
with tab_records:
    st.subheader("Employee Records")
    search = st.text_input("Search by name, department, job title, or ID")

    search_clause = ""
    search_params = list(PARAMS)
    if search:
        piece = '("Full Name" LIKE ? OR Department LIKE ? OR "Job Title" LIKE ? OR Employee_ID LIKE ?)'
        term = f"%{search}%"
        search_clause = (" AND " if WHERE else "WHERE ") + piece
        search_params += [term, term, term, term]

    count_sql = f"SELECT COUNT(*) AS n FROM employees {WHERE}{search_clause}"
    total_rows = run_query(count_sql, tuple(search_params)).iloc[0]["n"]

    page_size = 25
    max_page = max(0, (total_rows - 1) // page_size)
    page = st.number_input("Page", min_value=0, max_value=int(max_page), value=0, step=1)

    records_sql = f"""
        SELECT Employee_ID AS ID, "Full Name", Department, "Job Title", Gender, Age,
               "Education Level", Salary, "Performance Rating", Status
        FROM employees {WHERE}{search_clause}
        ORDER BY Salary DESC
        LIMIT {page_size} OFFSET {page * page_size}
    """
    records = run_query(records_sql, tuple(search_params))
    st.dataframe(
        records,
        width='stretch',
        hide_index=True,
        column_config={"Salary": st.column_config.NumberColumn(format="$%d")},
    )
    st.caption(f"Showing {page*page_size+1}-{min(total_rows,(page+1)*page_size)} of {total_rows:,} employees")

st.divider()
st.caption("Data: 8,950 employee records · every chart above is powered by a live SQL query against db/hr.db — see sql/queries.sql")
