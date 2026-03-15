import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import create_engine

load_dotenv()
api_key = os.getenv('GROQ_API_KEY')
client = Groq(api_key=api_key)
engine = create_engine('sqlite:///db/finsight.db')

DB_SCHEMA = """
You are a financial data analyst for Traxovian Inc., a mid-market SaaS company.
You have access to a SQLite database with these tables:

1. revenue
   columns: transaction_id, date, month, quarter, year, type, sub_type,
            product, plan, customer_id, sales_rep, region, department,
            amount, currency, payment_terms, payment_status, churn_risk

2. expenses
   columns: transaction_id, date, month, quarter, year, type, category,
            sub_category, vendor_id, department, amount, currency,
            approval_status, payment_method

3. payroll
   columns: payroll_id, date, month, quarter, year, employee_id, department,
            role, employment_type, base_salary_annual, gross_monthly_pay,
            bonus, taxes_withheld, net_pay, currency, status

4. budget_vs_actual
   columns: budget_id, period, quarter, year, department, category,
            budget_amount, actual_amount, variance, variance_pct, status

STRICT RULES:
- Return ONLY a valid SQLite SQL query. Nothing else.
- No markdown. No backticks. No explanation. Just the raw SQL.
- Use SUM(), AVG(), COUNT(), GROUP BY, ORDER BY where needed.
- Revenue questions → use the revenue table.
- Cost or spending questions → use the expenses table.
- Payroll questions → use the payroll table.
- Budget questions → use the budget_vs_actual table.
- All amount columns are in USD.
"""

def ask_question(user_question):
    print(f'\n  Question  : {user_question}')
    print('  Thinking...')

    
    sql_response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        temperature=0,              
        max_tokens=500,
        messages=[
            {
                'role': 'system',
                'content': DB_SCHEMA
            },
            {
                'role': 'user',
                'content': f'Write a SQLite SQL query to answer this: {user_question}'
            }
        ]
    )
    sql_query = sql_response.choices[0].message.content.strip()
    # print(f'  SQL Query : {sql_query}')

    
    try:
        with engine.connect() as conn:
            result_df = pd.read_sql(sql_query, conn)

        print(f'  Rows returned : {len(result_df)}')

        
        explain_response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            temperature=0.3,        
            max_tokens=300,
            messages=[
                {
                    'role': 'user',
                    'content': f"""
The user asked: "{user_question}"
The database returned this data: {result_df.to_string()}

Write a 2-3 sentence plain English summary of this result
as a financial analyst presenting to an executive at Traxovian Inc.
Be specific with numbers. Keep it concise and professional.
"""
                }
            ]
        )
        explanation = explain_response.choices[0].message.content.strip()

        return {
            'question':    user_question,
            'sql':         sql_query,
            'result':      result_df,
            'explanation': explanation,
            'error':       None
        }

    except Exception as e:
        return {
            'question':    user_question,
            'sql':         sql_query,
            'result':      None,
            'explanation': None,
            'error':       str(e)
        }


if __name__ == '__main__':

    test_questions = [
        "What was the total revenue in 2023?",
        "Which region generated the most revenue?",
        "What are the top 3 expense categories?",
        "Which department has the highest payroll cost?",
        "How many transactions had overdue payment status?",
    ]

    print('=' * 60)
    print('  FinSight AI Copilot')
    print('=' * 60)

    for q in test_questions:
        output = ask_question(q)

        if output['error']:
            print(f'  ERROR : {output["error"]}')
        else:
            print(f'\n  Result:')
            print(output['result'].to_string(index=False))
            print(f'\n  Explanation: {output["explanation"]}')

        print('\n' + '-' * 60)