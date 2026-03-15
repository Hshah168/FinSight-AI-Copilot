from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///db/finsight.db')

print('FinSight AI Copilot — Database Verification')
print('=' * 45)
with engine.connect() as conn:
    tables = ['revenue', 'expenses', 'payroll', 'budget_vs_actual',
              'financial_metrics', 'forecast_results']
    total = 0
    for t in tables:
        n = conn.execute(text(f'SELECT COUNT(*) FROM {t}')).fetchone()[0]
        total += n
        print(f'  {t:<25}: {n:>6,} rows')
    print('=' * 45)
    print(f'  {"TOTAL":<25}: {total:>6,} rows')