import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///db/finsight.db')
tables = ['expenses','budget_vs_actual','ai_sessions','ai_daily_cost','ai_alerts']

for t in tables:
    try:
        df = pd.read_sql(f'SELECT COUNT(*) as n FROM {t}', engine)
        print(f'{t}: OK  {df["n"][0]} rows')
    except Exception as e:
        print(f'{t}: MISSING  {e}')