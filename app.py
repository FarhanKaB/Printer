import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

st.set_page_config(
    page_title="Printer BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st_autorefresh(interval=30_000, key="dashboard_refresh")

PAGE_STYLE = """
<style>
body { background-color: #070d1a; color: #e8eef7; }
section.main { background-color: #0b1626; }
.css-1d391kg { background-color: #0b1626 !important; }
.css-18e3th9 { background-color: #0b1626 !important; }
.css-1lcbmhc { background-color: #0b1626 !important; }
.css-1y4p8pa { background-color: #0b1626 !important; }
.stButton>button { background-color: #0f1720; color: #f8fafc; }
.stButton>button:hover { background-color: #1f2937; }
.e1fqkh3o3, .e1fqkh3o2 { background-color: #0f1720 !important; }
.css-15tx938 { background-color: #0b1626 !important; }
.css-1vq4p4u, .css-18ni7ap { color: #e8eef7 !important; }
.css-1q8dd3e { color: #f8fafc !important; }
</style>
"""

st.markdown(PAGE_STYLE, unsafe_allow_html=True)

st.markdown(
    """
    <div style='display:flex; justify-content:space-between; align-items:center; gap:16px;'>
        <div>
            <h1 style='margin:0; color:#f8fafc'>Printer BI Dashboard</h1>
            <p style='margin:5px 0 0; color:#cbd5e1'>Modern real-time reporting for Neon PostgreSQL print operations.</p>
        </div>
        <div style='padding:14px 20px; border-radius:18px; background:#111827; border:1px solid rgba(255,255,255,0.08); color:#cbd5e1;'>
            Auto refresh: <strong>30 seconds</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def get_db_params():
    return {
        "host": os.getenv("DB_HOST", ""),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", ""),
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", ""),
        "sslmode": os.getenv("DB_SSLMODE", "require"),
    }


def get_connection():
    params = get_db_params()
    if not all([params["host"], params["dbname"], params["user"], params["password"]]):
        st.error("Please set Neon PostgreSQL credentials in environment variables or a .env file.")
        st.info("Required: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, optional: DB_SSLMODE")
        st.stop()

    return psycopg2.connect(**params)


@st.cache_data(ttl=30)
def load_data():
    with get_connection() as conn:
        employees = pd.read_sql_query(
            "SELECT id, employee_name, department, created_at FROM employees ORDER BY employee_name",
            conn,
            parse_dates=["created_at"],
        )
        printers = pd.read_sql_query(
            "SELECT id, printer_name, location, model, created_at FROM printers ORDER BY printer_name",
            conn,
            parse_dates=["created_at"],
        )
        print_logs = pd.read_sql_query(
            """
            SELECT
                l.id,
                e.employee_name,
                p.printer_name,
                l.document_name,
                l.pages_printed,
                l.print_time,
                l.captured_at
            FROM print_logs l
            JOIN employees e ON e.id = l.employee_id
            JOIN printers p ON p.id = l.printer_id
            ORDER BY l.print_time DESC
            """,
            conn,
            parse_dates=["print_time", "captured_at"],
        )
        collected_jobs = pd.read_sql_query(
            "SELECT id, job_id, printer_name, collected_at FROM collected_jobs ORDER BY collected_at DESC",
            conn,
            parse_dates=["collected_at"],
        )

    return employees, printers, print_logs, collected_jobs


employees, printers, print_logs, collected_jobs = load_data()

if print_logs.empty:
    st.warning("No print logs found in the database. Add some print jobs to see analytics.")
    st.stop()

print_logs["print_date"] = print_logs["print_time"].dt.date

sidebar = st.sidebar
sidebar.header("Report filters")
selected_employees = sidebar.multiselect(
    "Employee",
    options=["All"] + employees["employee_name"].tolist(),
    default=["All"],
)
selected_printers = sidebar.multiselect(
    "Printer",
    options=["All"] + printers["printer_name"].tolist(),
    default=["All"],
)

min_date = print_logs["print_time"].dt.date.min()
max_date = print_logs["print_time"].dt.date.max()
selected_dates = sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

sidebar.markdown("---")
sidebar.markdown("### Neon PostgreSQL connection")
sidebar.write(f"**Host:** {get_db_params()['host']}:{get_db_params()['port']}")
sidebar.write(f"**Database:** {get_db_params()['dbname']}")
sidebar.success("Connected")

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates
    end_date = selected_dates

filtered = print_logs.copy()
if "All" not in selected_employees:
    filtered = filtered[filtered["employee_name"].isin(selected_employees)]
if "All" not in selected_printers:
    filtered = filtered[filtered["printer_name"].isin(selected_printers)]
filtered = filtered[
    (filtered["print_time"].dt.date >= start_date) &
    (filtered["print_time"].dt.date <= end_date)
]

if filtered.empty:
    st.warning("No data matches the selected filters. Try a wider date range or remove some filters.")

metrics = st.columns(4)
metrics[0].metric("Total Prints", f"{int(filtered['pages_printed'].sum()):,}")
metrics[1].metric("Active Printers", filtered["printer_name"].nunique())
metrics[2].metric("Employees", filtered["employee_name"].nunique())
metrics[3].metric("Print Jobs", filtered.shape[0])

st.markdown("---")

trend_data = (
    filtered.groupby(filtered["print_date"])
    .agg(pages_printed=("pages_printed", "sum"), jobs=("id", "count"))
    .reset_index()
)

employee_rank = (
    filtered.groupby("employee_name")
    .agg(pages_printed=("pages_printed", "sum"), jobs=("id", "count"))
    .sort_values("pages_printed", ascending=False)
    .head(10)
    .reset_index()
)

printer_rank = (
    filtered.groupby("printer_name")
    .agg(pages_printed=("pages_printed", "sum"), jobs=("id", "count"))
    .sort_values("pages_printed", ascending=False)
    .head(10)
    .reset_index()
)

line_chart = px.line(
    trend_data,
    x="print_date",
    y="pages_printed",
    title="Daily Print Trend",
    labels={"print_date": "Date", "pages_printed": "Pages Printed"},
    template="plotly_dark",
)
line_chart.update_traces(mode="lines+markers", line=dict(color="#3b82f6", width=3))
line_chart.update_layout(hovermode="x unified")

top_employee_chart = px.bar(
    employee_rank,
    x="pages_printed",
    y="employee_name",
    orientation="h",
    title="Top Employees by Pages",
    labels={"pages_printed": "Pages", "employee_name": "Employee"},
    template="plotly_dark",
)
top_employee_chart.update_layout(yaxis=dict(autorange="reversed"))

printer_usage_chart = px.bar(
    printer_rank,
    x="printer_name",
    y="pages_printed",
    title="Printer Usage",
    labels={"printer_name": "Printer", "pages_printed": "Pages Printed"},
    template="plotly_dark",
)
printer_usage_chart.update_layout(xaxis_tickangle=-45)

chart_col1, chart_col2 = st.columns((2, 1))
chart_col1.plotly_chart(line_chart, use_container_width=True)
chart_col2.plotly_chart(top_employee_chart, use_container_width=True)

st.markdown("---")
row1, row2 = st.columns((2, 1))
row1.plotly_chart(printer_usage_chart, use_container_width=True)
row2.subheader("Latest Collected Jobs")
row2.dataframe(
    collected_jobs.head(8)[["job_id", "printer_name", "collected_at"]],
    hide_index=True,
    use_container_width=True,
)

st.markdown("---")
st.subheader("Recent Print Jobs")
st.dataframe(
    filtered[
        ["print_time", "employee_name", "printer_name", "document_name", "pages_printed", "captured_at"]
    ].rename(columns={
        "print_time": "Print Time",
        "employee_name": "Employee",
        "printer_name": "Printer",
        "document_name": "Document",
        "pages_printed": "Pages",
        "captured_at": "Captured At",
    }),
    hide_index=True,
    use_container_width=True,
)

st.caption(
    f"Data refreshed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Filtered range: {start_date} to {end_date}"
)
