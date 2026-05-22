# Printer BI Dashboard

A beginner-friendly Streamlit dashboard built to connect directly to Neon PostgreSQL and display real-time print analytics.

## Features

- Real-time auto-refresh every 30 seconds
- Modern Power BI-style dark UI
- KPI cards for print totals, printers, and employees
- Plotly charts for daily trends, top employees, and printer usage
- Recent print jobs table
- Sidebar filters for employee, printer, and date range
- Neon PostgreSQL connection using environment variables

## Project Structure

```
project/
│
├── app.py
├── requirements.txt
├── README.md
└── .env.example
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy the environment example:

```bash
cp .env.example .env
```

3. Open `.env` and fill your Neon PostgreSQL credentials.

4. Run the Streamlit app:

```bash
streamlit run app.py
```

5. Open the local URL shown in the terminal.

## Neon Schema

Use your existing tables in Neon PostgreSQL:

- `employees`
- `printers`
- `print_logs`
- `collected_jobs`

The dashboard expects the schema constructed from your provided SQL.

## Notes

- The app refreshes automatically every 30 seconds using `streamlit-autorefresh`.
- If you use a `.env` file, make sure it is loaded in the same folder as `app.py`.
- Use `DB_SSLMODE=require` for Neon when SSL is required.
