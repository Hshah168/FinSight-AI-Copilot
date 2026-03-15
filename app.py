import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

engine = create_engine('sqlite:///db/finsight.db')

@st.cache_data
def load_table(table_name):
    return pd.read_sql(f'SELECT * FROM {table_name}', engine)

st.set_page_config(
    page_title='FinSight AI Copilot',
    page_icon='📊',
    layout='wide'
)

st.sidebar.title(' FinSight AI Copilot')
st.sidebar.markdown('**Company:** Traxovian Inc.')
st.sidebar.markdown('**Data:** 2020 – 2025')
st.sidebar.markdown('---')
page = st.sidebar.radio(
    'Navigate',
    [' Executive Dashboard', ' Ask AI', ' Raw Data']
)

# ════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE DASHBOARD
# ════════════════════════════════════════════════════════════════
if page == ' Executive Dashboard':

    st.title(' FinSight AI Copilot')
    st.markdown('### Traxovian Inc. — Financial Performance 2020–2025')
    st.markdown('---')

    # Load data
    revenue_df = load_table('revenue')
    expense_df = load_table('expenses')
    payroll_df = load_table('payroll')
    bva_df     = load_table('budget_vs_actual')

    # KPI Cards 
    total_rev    = revenue_df['amount'].sum()
    total_exp    = expense_df['amount'].sum()
    total_pay    = payroll_df['gross_monthly_pay'].sum()
    cogs         = expense_df[expense_df['category'] == 'COGS']['amount'].sum()
    gross_profit = total_rev - cogs
    gross_margin = (gross_profit / total_rev * 100) if total_rev else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(' Total Revenue',  f'${total_rev:,.0f}')
    col2.metric(' Total Expenses', f'${total_exp:,.0f}')
    col3.metric(' Total Payroll',  f'${total_pay:,.0f}')
    col4.metric(' Gross Margin',   f'{gross_margin:.1f}%')

    st.markdown('---')

    # Row 1: Revenue by Year + Revenue by Region
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(' Revenue by Year')
        rev_by_year = revenue_df.groupby('year')['amount'].sum().reset_index()
        fig = px.bar(
            rev_by_year, x='year', y='amount',
            labels={'amount': 'Revenue (USD)', 'year': 'Year'},
            color_discrete_sequence=['#2196F3']
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader(' Revenue by Region')
        rev_by_region = revenue_df.groupby('region')['amount'].sum().reset_index()
        fig = px.pie(
            rev_by_region, names='region', values='amount'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Row 2: Revenue by Product + Expense Breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(' Revenue by Product')
        rev_by_product = revenue_df.groupby('product')['amount'].sum().reset_index()
        fig = px.bar(
            rev_by_product, x='product', y='amount',
            color='product',
            labels={'amount': 'Revenue (USD)', 'product': 'Product'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader(' Expense Breakdown')
        exp_by_cat = expense_df.groupby('category')['amount'].sum().reset_index()
        fig = px.pie(
            exp_by_cat, names='category', values='amount'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Row 3: Monthly Revenue Trend
    st.subheader(' Monthly Revenue Trend')
    rev_monthly = revenue_df.groupby('month')['amount'].sum().reset_index()
    rev_monthly = rev_monthly.sort_values('month')
    fig = px.line(
        rev_monthly, x='month', y='amount',
        labels={'amount': 'Revenue (USD)', 'month': 'Month'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Row 4: Budget vs Actual
    st.subheader(' Budget vs Actual by Department')
    bva_summary = bva_df.groupby('department')[['budget_amount', 'actual_amount']].sum().reset_index()
    fig = px.bar(
        bva_summary, x='department',
        y=['budget_amount', 'actual_amount'],
        barmode='group',
        labels={'value': 'Amount (USD)', 'department': 'Department'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Row 5: Payroll by Department
    st.subheader(' Payroll by Department')
    pay_by_dept = payroll_df.groupby('department')['gross_monthly_pay'].sum().reset_index()
    fig = px.bar(
        pay_by_dept, x='department', y='gross_monthly_pay',
        color='department',
        labels={'gross_monthly_pay': 'Total Payroll (USD)', 'department': 'Department'}
    )
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════
# PAGE 2 — ASK AI
# ════════════════════════════════════════════════════════════════
elif page == ' Ask AI':

    st.title(' Ask FinSight AI')
    st.markdown('Type any financial question about Traxovian Inc. in plain English.')
    st.markdown('---')

    from ai_engine import ask_question

   
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    
    st.markdown('**Click a question to try it:**')
    examples = [
        "What was the total revenue in 2023?",
        "Which region generated the most revenue?",
        "What are the top 3 expense categories?",
        "Which department has the highest payroll?",
        "How many invoices are overdue?",
        "Which product made the most revenue?",
        "What was revenue in 2020 vs 2024?",
        "What is the total budget variance?",
    ]

    cols = st.columns(4)
    for i, example in enumerate(examples):
        if cols[i % 4].button(example, key=f'btn_{i}'):
            st.session_state['prefill'] = example

    st.markdown('---')

 
    user_input = st.text_input(
        ' Your question:',
        value=st.session_state.get('prefill', ''),
        placeholder='e.g. What was total revenue in 2023?'
    )

    if st.button(' Ask FinSight AI', type='primary'):
        if user_input.strip() == '':
            st.warning('Please type a question first.')
        else:
            with st.spinner('Thinking...'):
                output = ask_question(user_input)
            st.session_state.chat_history.insert(0, output)
            if 'prefill' in st.session_state:
                del st.session_state['prefill']


    if st.session_state.chat_history:
        for item in st.session_state.chat_history:
            with st.container():
                st.markdown(f'** Question:** {item["question"]}')

                if item['error']:
                    st.error(f' Error: {item["error"]}')
                else:
                    st.code(item['sql'], language='sql')
                    st.success(item['explanation'])
                    if item['result'] is not None and not item['result'].empty:
                        st.dataframe(item['result'], use_container_width=True)
                st.markdown('---')
    else:
        st.info(' Click a question above or type your own to get started.')

# ════════════════════════════════════════════════════════════════
# PAGE 3 — RAW DATA
# ════════════════════════════════════════════════════════════════
elif page == ' Raw Data':

    st.title(' Raw Data Explorer')
    st.markdown('Browse the underlying data powering FinSight AI.')
    st.markdown('---')

    table_choice = st.selectbox(
        'Select a table:',
        ['revenue', 'expenses', 'payroll', 'budget_vs_actual']
    )

    df = load_table(table_choice)

    col1, col2, col3 = st.columns(3)
    col1.metric('Total Rows',    f'{len(df):,}')
    col2.metric('Total Columns', f'{len(df.columns)}')
    col3.metric('Date Range',    f"{df['year'].min()} – {df['year'].max()}" if 'year' in df.columns else 'N/A')

    st.markdown('---')

    # Year filter
    if 'year' in df.columns:
        years = ['All'] + sorted([str(y) for y in df['year'].unique()])
        selected_year = st.selectbox('Filter by year:', years)
        if selected_year != 'All':
            df = df[df['year'] == int(selected_year)]

    st.dataframe(df, use_container_width=True, height=500)

    # Download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label='⬇ Download as CSV',
        data=csv,
        file_name=f'traxovian_{table_choice}.csv',
        mime='text/csv'
    )