import pandas as pd
from data_loader import load_file
from data_processor import clean_dataframe, calculate_kpis
from sqlalchemy import create_engine

engine = create_engine('sqlite:///db/finsight.db')

FILES = {
    'uploads/traxovian_revenue.csv':            'revenue',
    'uploads/traxovian_expenses.csv':           'expenses',
    'uploads/traxovian_payroll.csv':            'payroll',
    'uploads/traxovian_budget_vs_actual.csv':   'budget_vs_actual',
    'uploads/traxovian_ai_sessions.csv':          'ai_sessions',
    'uploads/traxovian_ai_alerts.csv':            'ai_alerts',
    'uploads/traxovian_ai_daily.csv':             'ai_daily_cost',
}

def run_pipeline():
    loaded = {}

    print('=' * 55)
    print('  FinSight AI Copilot — Loading Data into Database')
    print('=' * 55)

    for filepath, table in FILES.items():
        df = load_file(filepath)        
        df = clean_dataframe(df)           
        df.to_sql(                        
            table,
            engine,
            if_exists='replace',        
            index=False                   
        )
        print(f' Saved {len(df):,} rows → [{table}]')
        loaded[table] = df

    print('\n' + '=' * 55)
    print(' KPI Summary — Traxovian Inc.')
    print('=' * 55)
    kpis = calculate_kpis(
        loaded['revenue'],
        loaded['expenses'],
        loaded['payroll']
    )
    for k, v in kpis.items():
        print(f'  {k:<25} :  ${v:>15,.2f}')

    print('=' * 55)
    print(' Pipeline complete. Database is ready.')
    print('=' * 55)

if __name__ == '__main__':
    run_pipeline()