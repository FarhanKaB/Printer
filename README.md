# 🖨️ Print Management Dashboard

A modern, real-time Power BI-style dashboard built with Streamlit and Neon PostgreSQL. Monitor printing analytics, employee activity, and printer usage with auto-refreshing visualizations.

![Dashboard Features](https://img.shields.io/badge/Features-KPIs%20|%20Charts%20|%20Analytics%20|%20Filters-blue)
![Real-time](https://img.shields.io/badge/Real--time-30s%20refresh-green)
![Framework](https://img.shields.io/badge/Framework-Streamlit-red)
![Database](https://img.shields.io/badge/Database-Neon%20PostgreSQL-black)

## ✨ Features

### 📊 Dashboard Components
- **KPI Cards**: Display key metrics (Total Prints, Active Printers, Total Employees, Total Pages)
- **Daily Print Trends**: Line chart showing printing patterns over time
- **Top Printers**: Bar chart of most-used printers with page counts
- **Top Employees**: Ranking of most active employees
- **Recent Print Jobs**: Detailed table of latest print activities
- **Auto-Refresh**: Updates every 30 seconds automatically

### 🎯 Filters & Controls
- **Date Range Filter**: Select custom date ranges for analysis
- **Employee Filter**: Filter jobs by specific employees
- **Printer Filter**: Filter jobs by specific printers
- **Real-time Updates**: All visualizations update automatically

### 🎨 Design Features
- **Dark Professional Theme**: Modern, eye-friendly dark UI
- **Responsive Layout**: Works on desktop and tablets
- **Power BI-Style Cards**: Professional KPI metrics display
- **Interactive Charts**: Plotly visualizations with hover details
- **Performance Optimized**: Caching reduces database queries

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Neon PostgreSQL database with tables created
- Git (optional)

### 1. Clone/Download the Project
```bash
cd /workspaces/Printer
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
# Linux/Mac
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your Neon PostgreSQL credentials:
```
DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-1.neon.tech/dbname?sslmode=require
```

Or use individual parameters:
```
DB_HOST=ep-xxxxx.us-east-1.neon.tech
DB_NAME=your_database_name
DB_USER=your_user
DB_PASSWORD=your_password
DB_PORT=5432
```

### 5. Run the Dashboard
```bash
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

## 📦 Project Structure

```
project/
├── app.py                 # Main dashboard application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your actual credentials (not in git)
└── README.md             # This file
```

## 🗄️ Database Schema

The dashboard connects to four main tables:

### employees
```sql
- id (SERIAL PRIMARY KEY)
- employee_name (TEXT UNIQUE)
- department (TEXT)
- created_at (TIMESTAMPTZ)
```

### printers
```sql
- id (SERIAL PRIMARY KEY)
- printer_name (TEXT UNIQUE)
- location (TEXT)
- model (TEXT)
- created_at (TIMESTAMPTZ)
```

### print_logs
```sql
- id (SERIAL PRIMARY KEY)
- employee_id (FK → employees)
- printer_id (FK → printers)
- document_name (TEXT)
- pages_printed (INTEGER)
- print_time (TIMESTAMPTZ)
- captured_at (TIMESTAMPTZ)
```

### collected_jobs
```sql
- id (SERIAL PRIMARY KEY)
- job_id (TEXT UNIQUE)
- printer_name (TEXT)
- collected_at (TIMESTAMPTZ)
```

## 📊 Key Metrics

The dashboard displays and calculates:

1. **Total Prints**: Count of all print jobs ever recorded
2. **Active Printers**: Number of unique printers used in the last 7 days
3. **Total Employees**: Count of registered employees
4. **Total Pages**: Sum of all pages printed
5. **Daily Trends**: Print volume and page count by day
6. **Employee Rankings**: Top employees by activity
7. **Printer Usage**: Which printers are most used

## ⚙️ Configuration

### Cache Settings
The app uses 30-second caching (`ttl=30`) for:
- KPI metrics
- Employee lists
- Printer lists
- Print trends
- Top employees
- Printer usage
- Recent print jobs

Adjust the `ttl` value in any `@st.cache_data(ttl=X)` decorator to change cache duration.

### Refresh Interval
Default auto-refresh is every 30 seconds. To change:
- Edit line at the end of `app.py`: `time.sleep(30)`
- Change `30` to your desired seconds

### Database Query Limits
- Recent jobs table displays up to 100 records (configurable)
- Top employees/printers limited to 10 records (customizable)

## 🔒 Security Best Practices

1. **Never commit `.env` file**: Add to `.gitignore`
2. **Use connection pooling**: Connection is cached per Streamlit session
3. **Neon SSL**: All connections use SSL by default (`sslmode=require`)
4. **Credentials**: Keep Neon passwords secure in environment variables

## 🛠️ Deployment

### Deploy to Streamlit Cloud (Free)

1. Push your repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and connect your GitHub repo
4. Set environment variables in the Streamlit Cloud settings:
   - Add `DATABASE_URL` or individual DB credentials
5. Deploy!

### Deploy to Other Platforms
- **Heroku**: Use Procfile: `web: streamlit run app.py`
- **Railway**: Connect GitHub repo and set environment variables
- **Render**: Similar to Railway, set environment variables
- **PythonAnywhere**: Upload and configure WSGI

## 🐛 Troubleshooting

### Database Connection Error
```
❌ Database Connection Error: [error message]
```
**Solution**: 
- Check DATABASE_URL or individual parameters in `.env`
- Ensure Neon database is running
- Verify firewall/network access
- Test connection manually: `psql [connection-string]`

### No Data Showing
- Verify data exists in your Neon database
- Check date range filter isn't too restrictive
- Try clearing browser cache: `Cmd/Ctrl + Shift + Delete`

### Slow Dashboard
- Dashboard caches data for 30 seconds - wait before refreshing
- Check Neon database performance
- Reduce query limits in code if needed
- Add indexes to frequently filtered columns

### Connection Timeout
- Neon free tier may have connection limits
- Reduce concurrent connections
- Use connection pooling (already implemented)

## 📈 Performance Tips

1. **Indexing**: Add indexes to frequently queried columns:
   ```sql
   CREATE INDEX idx_print_logs_employee ON print_logs(employee_id);
   CREATE INDEX idx_print_logs_printer ON print_logs(printer_id);
   CREATE INDEX idx_print_logs_time ON print_logs(print_time);
   ```

2. **Data Archival**: Archive old print logs to maintain performance
   ```sql
   -- Archive logs older than 1 year
   DELETE FROM print_logs WHERE print_time < NOW() - INTERVAL '1 year';
   ```

3. **Query Optimization**: Use EXPLAIN ANALYZE to optimize slow queries
   ```sql
   EXPLAIN ANALYZE SELECT ... FROM print_logs WHERE ...;
   ```

## 🚀 Advanced Features

### Add More Metrics
Edit `get_kpi_metrics()` function to add new calculations.

### Customize Charts
Modify Plotly chart configurations in the main dashboard section for different colors, styles, etc.

### Add Notifications
Integrate Streamlit alerts for specific events (e.g., print job failures).

### Export Data
Add download buttons for CSV exports using `st.download_button()`.

## 📚 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | 1.28.1 | Web framework |
| streamlit-autorefresh | 0.0.3 | Auto-refresh functionality |
| plotly | 5.17.0 | Interactive charts |
| pandas | 2.0.3 | Data manipulation |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |
| python-dotenv | 1.0.0 | Environment variables |

## 📝 License

Free to use and modify. Enjoy! 🎉

## 🤝 Contributing

Feel free to modify and extend this dashboard for your needs!

### Suggested Enhancements
- [ ] Add printer maintenance alerts
- [ ] Implement cost tracking per page
- [ ] Add anomaly detection for unusual patterns
- [ ] Create predictive maintenance warnings
- [ ] Add email notifications
- [ ] Implement user authentication

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Neon documentation: https://neon.tech/docs
3. Check Streamlit docs: https://docs.streamlit.io
4. Check Plotly docs: https://plotly.com/python

---

**Last Updated**: 2026-05-22
**Dashboard Version**: 1.0.0
**Status**: ✅ Production Ready

Happy Dashboarding! 🎉📊
