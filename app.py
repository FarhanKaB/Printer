import streamlit as st
from streamlit_autorefresh import rerun_if_updated
import psycopg2
from psycopg2 import sql
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Print Dashboard",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #0066cc;
        --secondary-color: #00d9ff;
        --success-color: #00b341;
        --warning-color: #ff9500;
        --danger-color: #ff3333;
    }
    
    /* Dark theme */
    .stApp {
        background-color: #0f1419;
        color: #ffffff;
    }
    
    /* KPI Card Styling */
    [data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        border-left: 4px solid #0066cc;
    }
    
    /* Sidebar styling */
    [data-testid="sidebar"] {
        background-color: #1a1f2e;
    }
    
    /* Remove whitespace */
    .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================
@st.cache_resource
def get_db_connection():
    """Create and cache database connection"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        if DATABASE_URL:
            # Use DATABASE_URL if provided
            conn = psycopg2.connect(DATABASE_URL)
        else:
            # Use individual parameters
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT", 5432),
                sslmode="require"
            )
        return conn
    except Exception as e:
        st.error(f"❌ Database Connection Error: {str(e)}")
        st.stop()

# ============================================================================
# QUERY FUNCTIONS WITH CACHING
# ============================================================================
@st.cache_data(ttl=30)
def get_kpi_metrics():
    """Get KPI metrics - cached for 30 seconds"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total prints
        cursor.execute("SELECT COUNT(*) FROM print_logs")
        total_prints = cursor.fetchone()[0]
        
        # Active printers
        cursor.execute("SELECT COUNT(DISTINCT printer_id) FROM print_logs WHERE print_time > NOW() - INTERVAL '7 days'")
        active_printers = cursor.fetchone()[0]
        
        # Total employees
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = cursor.fetchone()[0]
        
        # Total pages printed
        cursor.execute("SELECT COALESCE(SUM(pages_printed), 0) FROM print_logs")
        total_pages = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "total_prints": total_prints,
            "active_printers": active_printers,
            "total_employees": total_employees,
            "total_pages": total_pages
        }
    except Exception as e:
        st.error(f"Error fetching KPI metrics: {str(e)}")
        return {"total_prints": 0, "active_printers": 0, "total_employees": 0, "total_pages": 0}

@st.cache_data(ttl=30)
def get_employees_list():
    """Get list of employees - cached for 30 seconds"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT id, employee_name FROM employees ORDER BY employee_name", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching employees: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_printers_list():
    """Get list of printers - cached for 30 seconds"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT id, printer_name FROM printers ORDER BY printer_name", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching printers: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_daily_print_trends(start_date, end_date):
    """Get daily print trends - cached for 30 seconds"""
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                DATE(print_time) as date,
                COUNT(*) as print_count,
                SUM(pages_printed) as total_pages
            FROM print_logs
            WHERE print_time >= %s AND print_time <= %s
            GROUP BY DATE(print_time)
            ORDER BY DATE(print_time)
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching daily trends: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_top_employees(start_date, end_date, limit=10):
    """Get top employees by print count - cached for 30 seconds"""
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                e.employee_name,
                COUNT(pl.id) as print_count,
                SUM(pl.pages_printed) as total_pages
            FROM print_logs pl
            JOIN employees e ON pl.employee_id = e.id
            WHERE pl.print_time >= %s AND pl.print_time <= %s
            GROUP BY e.employee_name
            ORDER BY print_count DESC
            LIMIT %s
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date, limit))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching top employees: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_printer_usage(start_date, end_date):
    """Get printer usage statistics - cached for 30 seconds"""
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                p.printer_name,
                COUNT(pl.id) as print_count,
                SUM(pl.pages_printed) as total_pages,
                p.location
            FROM print_logs pl
            JOIN printers p ON pl.printer_id = p.id
            WHERE pl.print_time >= %s AND pl.print_time <= %s
            GROUP BY p.printer_name, p.location
            ORDER BY print_count DESC
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching printer usage: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_recent_print_jobs(employee_id=None, printer_id=None, start_date=None, end_date=None, limit=50):
    """Get recent print jobs with optional filters - cached for 30 seconds"""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                pl.id,
                e.employee_name,
                p.printer_name,
                pl.document_name,
                pl.pages_printed,
                pl.print_time
            FROM print_logs pl
            JOIN employees e ON pl.employee_id = e.id
            JOIN printers p ON pl.printer_id = p.id
            WHERE 1=1
        """
        params = []
        
        if employee_id and employee_id != "All":
            query += " AND pl.employee_id = %s"
            params.append(employee_id)
        
        if printer_id and printer_id != "All":
            query += " AND pl.printer_id = %s"
            params.append(printer_id)
        
        if start_date:
            query += " AND pl.print_time >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND pl.print_time <= %s"
            params.append(end_date)
        
        query += " ORDER BY pl.print_time DESC LIMIT %s"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['print_time'] = pd.to_datetime(df['print_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return df
    except Exception as e:
        st.error(f"Error fetching recent print jobs: {str(e)}")
        return pd.DataFrame()

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
st.sidebar.title("🎯 Filters")
st.sidebar.markdown("---")

# Date range filter
date_range = st.sidebar.date_input(
    "📅 Select Date Range",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

if len(date_range) == 2:
    start_date, end_date = date_range
    end_date = datetime.combine(end_date, datetime.max.time())
else:
    start_date = end_date = datetime.now()

# Employee filter
employees_df = get_employees_list()
employee_options = ["All"] + employees_df["employee_name"].tolist()
selected_employee = st.sidebar.selectbox("👤 Employee", employee_options)
employee_id = None
if selected_employee != "All":
    employee_id = employees_df[employees_df["employee_name"] == selected_employee]["id"].values[0]

# Printer filter
printers_df = get_printers_list()
printer_options = ["All"] + printers_df["printer_name"].tolist()
selected_printer = st.sidebar.selectbox("🖨️ Printer", printer_options)
printer_id = None
if selected_printer != "All":
    printer_id = printers_df[printers_df["printer_name"] == selected_printer]["id"].values[0]

# Refresh info
st.sidebar.markdown("---")
st.sidebar.info(
    "🔄 Dashboard auto-refreshes every 30 seconds\n\n"
    "Last updated: " + datetime.now().strftime("%H:%M:%S")
)

# ============================================================================
# MAIN DASHBOARD
# ============================================================================
st.title("🖨️ Print Management Dashboard")
st.markdown("Real-time printing analytics and monitoring")
st.markdown("---")

# KPI Section
st.subheader("📊 Key Performance Indicators")
kpis = get_kpi_metrics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📄 Total Prints",
        value=f"{kpis['total_prints']:,}",
        delta="All time"
    )

with col2:
    st.metric(
        label="🖨️ Active Printers",
        value=f"{kpis['active_printers']:,}",
        delta="Last 7 days"
    )

with col3:
    st.metric(
        label="👥 Total Employees",
        value=f"{kpis['total_employees']:,}",
        delta="Registered"
    )

with col4:
    st.metric(
        label="📑 Total Pages",
        value=f"{kpis['total_pages']:,}",
        delta="All time"
    )

st.markdown("---")

# Charts Section
st.subheader("📈 Analytics")

# Row 1: Daily Trends and Printer Usage
col1, col2 = st.columns([2, 1])

with col1:
    # Daily Print Trends
    daily_trends = get_daily_print_trends(start_date, end_date)
    
    if not daily_trends.empty:
        fig_daily = go.Figure()
        
        fig_daily.add_trace(go.Scatter(
            x=daily_trends['date'],
            y=daily_trends['print_count'],
            mode='lines+markers',
            name='Print Count',
            line=dict(color='#0066cc', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(0, 102, 204, 0.2)'
        ))
        
        fig_daily.update_layout(
            title="📅 Daily Print Trends",
            xaxis_title="Date",
            yaxis_title="Number of Prints",
            hovermode='x unified',
            template='plotly_dark',
            height=400,
            margin=dict(l=0, r=0, t=40, b=0),
            font=dict(color='white')
        )
        
        st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.info("No data available for the selected date range")

with col2:
    # Top Printers by Usage
    printer_usage = get_printer_usage(start_date, end_date)
    
    if not printer_usage.empty:
        top_printers = printer_usage.head(8)
        
        fig_printers = px.bar(
            top_printers,
            x='print_count',
            y='printer_name',
            orientation='h',
            color='total_pages',
            title="🖨️ Top Printers",
            labels={'print_count': 'Print Count', 'printer_name': 'Printer'},
            color_continuous_scale='Blues',
            height=400
        )
        
        fig_printers.update_layout(
            template='plotly_dark',
            showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0),
            font=dict(color='white'),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_printers, use_container_width=True)
    else:
        st.info("No printer data available")

# Row 2: Top Employees
top_employees = get_top_employees(start_date, end_date)

if not top_employees.empty:
    fig_employees = px.bar(
        top_employees.head(10),
        x='print_count',
        y='employee_name',
        orientation='h',
        color='total_pages',
        title="👥 Top Employees by Print Activity",
        labels={'print_count': 'Print Count', 'employee_name': 'Employee'},
        color_continuous_scale='Teal',
        height=400
    )
    
    fig_employees.update_layout(
        template='plotly_dark',
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        font=dict(color='white'),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig_employees, use_container_width=True)
else:
    st.info("No employee data available")

st.markdown("---")

# Recent Print Jobs Table
st.subheader("📋 Recent Print Jobs")

recent_jobs = get_recent_print_jobs(
    employee_id=employee_id,
    printer_id=printer_id,
    start_date=start_date,
    end_date=end_date,
    limit=100
)

if not recent_jobs.empty:
    # Format table display
    display_df = recent_jobs.copy()
    display_df.columns = ['ID', 'Employee', 'Printer', 'Document', 'Pages', 'Time']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.caption(f"Showing {len(display_df)} recent print jobs")
else:
    st.info("No print jobs found for the selected filters")

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 3rem;'>
    <p>🔄 Dashboard auto-refreshes every 30 seconds</p>
    <p style='color: #555;'>Last refresh: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh every 30 seconds
rerun_if_updated()
time.sleep(30)
st.rerun()
