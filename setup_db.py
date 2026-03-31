import os
import pandas as pd
from sqlalchemy import create_engine, text

os.makedirs('db', exist_ok=True)
engine = create_engine('sqlite:///db/finsight.db')

with engine.connect() as conn:
    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY,
        transaction_id TEXT, date TEXT, month TEXT, quarter TEXT, year INTEGER,
        type TEXT, sub_type TEXT, product TEXT, plan TEXT,
        customer_id TEXT, sales_rep TEXT, region TEXT, department TEXT,
        amount REAL, currency TEXT, payment_terms TEXT,
        payment_status TEXT, churn_risk TEXT, notes TEXT
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY,
        transaction_id TEXT, date TEXT, month TEXT, quarter TEXT, year INTEGER,
        type TEXT, category TEXT, sub_category TEXT,
        vendor_id TEXT, department TEXT, amount REAL, currency TEXT,
        approval_status TEXT, payment_method TEXT, notes TEXT
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY,
        payroll_id TEXT, date TEXT, month TEXT, quarter TEXT, year INTEGER,
        type TEXT, employee_id TEXT, department TEXT, role TEXT,
        employment_type TEXT, base_salary_annual REAL, gross_monthly_pay REAL,
        bonus REAL, taxes_withheld REAL, net_pay REAL, currency TEXT, status TEXT
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS budget_vs_actual (
        id INTEGER PRIMARY KEY,
        budget_id TEXT, period TEXT, quarter TEXT, year INTEGER,
        department TEXT, category TEXT, budget_amount REAL,
        actual_amount REAL, variance REAL, variance_pct REAL,
        status TEXT, approved_by TEXT
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS financial_metrics (
        id INTEGER PRIMARY KEY,
        metric_name TEXT, value REAL, period TEXT, calculated_at TEXT
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS forecast_results (
        id INTEGER PRIMARY KEY,
        period TEXT, forecast_value REAL, model_used TEXT, created_at TEXT
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS ai_sessions (
        session_id TEXT, timestamp TEXT, date TEXT, week TEXT,
        employee_id TEXT, department TEXT, product TEXT,
        ai_tool TEXT, model TEXT, provider TEXT, task_type TEXT,
        input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER,
        cost_usd REAL, time_saved_hrs REAL,
        value_generated REAL, roi_ratio REAL
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS ai_daily_cost (
        date TEXT, department TEXT, daily_cost REAL,
        sessions INTEGER, tokens INTEGER,
        monthly_budget REAL, cumulative_cost REAL, budget_used_pct REAL
    )'''))

    _ = conn.execute(text('''CREATE TABLE IF NOT EXISTS ai_alerts (
        alert_id TEXT, date TEXT, department TEXT,
        alert_type TEXT, threshold_pct REAL, actual_pct REAL,
        cumulative_cost REAL, monthly_budget REAL, overspend REAL
    )'''))

    conn.commit()

print('=' * 60)
print('        FinSight AI Copilot — Database Status')
print('=' * 60)

tables = ['revenue', 'expenses', 'payroll', 'budget_vs_actual',
          'financial_metrics', 'forecast_results']

total_rows = 0
with engine.connect() as conn:
    for table in tables:
        count = conn.execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()[0]
        total_rows += count
        print(f'\n TABLE: {table.upper()} — {count:,} rows')
        print('-' * 60)

        if count > 0:
            df = pd.read_sql(f'SELECT * FROM {table} LIMIT 2', engine)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 120)
            pd.set_option('display.max_colwidth', 15)
            print(df.to_string(index=False))
        else:
            print('  (empty — will be filled on Day 2)')

print('\n' + '=' * 60)
print(f'  TOTAL ROWS IN DATABASE : {total_rows:,}')
print('=' * 60)