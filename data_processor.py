import pandas as pd
from datetime import datetime

def clean_dataframe(df):
    df = df.dropna(how='all')
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    df = df.drop_duplicates()
    return df

def calculate_kpis(revenue_df, expense_df, payroll_df):
    total_rev    = revenue_df['amount'].sum()
    cogs         = expense_df[expense_df['category'] == 'COGS']['amount'].sum()
    rd           = expense_df[expense_df['category'] == 'R&D']['amount'].sum()
    sales_mkt    = expense_df[expense_df['category'] == 'Sales & Mkt']['amount'].sum()
    ga           = expense_df[expense_df['category'] == 'G&A']['amount'].sum()
    total_payroll= payroll_df['gross_monthly_pay'].sum()
    gross_profit = total_rev - cogs
    total_opex   = sales_mkt + rd + ga + total_payroll
    op_income    = gross_profit - total_opex

    return {
        'Total Revenue':       round(total_rev, 2),
        'COGS':                round(cogs, 2),
        'Gross Profit':        round(gross_profit, 2),
        'Gross Margin %':      round(gross_profit / total_rev * 100, 2) if total_rev else 0,
        'R&D Spend':           round(rd, 2),
        'Sales & Marketing':   round(sales_mkt, 2),
        'G&A':                 round(ga, 2),
        'Total Payroll':       round(total_payroll, 2),
        'Operating Income':    round(op_income, 2),
        'Operating Margin %':  round(op_income / total_rev * 100, 2) if total_rev else 0,
        'EBITDA (approx)':     round(op_income, 2),
    }