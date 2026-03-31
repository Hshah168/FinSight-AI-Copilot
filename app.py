import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv

engine = create_engine('sqlite:///db/finsight.db')

@st.cache_data
def load_table(table_name):
    return pd.read_sql(f'SELECT * FROM {table_name}', engine)

st.set_page_config(page_title='FinSight AI Copilot', page_icon='📊', layout='wide')

st.sidebar.title(' FinSight AI Copilot')
st.sidebar.markdown('**Company:** Traxovian Inc.')
st.sidebar.markdown('**Data:** 2020 – 2025')
st.sidebar.markdown('---')
page = st.sidebar.radio('Navigate', [
    'Executive Dashboard','FinOps Dashboard',
    'AI Cost Governance','Ask AI','Raw Data',
])

# ════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE DASHBOARD
# ════════════════════════════════════════════════════════════════
if page == 'Executive Dashboard':
    st.title(' FinSight AI Copilot')
    st.markdown('### Traxovian Inc. — Financial Performance 2020–2025')
    st.markdown('---')

    revenue_df = load_table('revenue')
    expense_df = load_table('expenses')
    payroll_df = load_table('payroll')
    bva_df     = load_table('budget_vs_actual')

    total_rev    = revenue_df['amount'].sum()
    total_exp    = expense_df['amount'].sum()
    total_pay    = payroll_df['gross_monthly_pay'].sum()
    cogs         = expense_df[expense_df['category']=='COGS']['amount'].sum()
    gross_profit = total_rev - cogs
    gross_margin = (gross_profit/total_rev*100) if total_rev else 0

    col1,col2,col3,col4 = st.columns(4)
    col1.metric(' Total Revenue',  f'${total_rev:,.0f}')
    col2.metric(' Total Expenses', f'${total_exp:,.0f}')
    col3.metric(' Total Payroll',  f'${total_pay:,.0f}')
    col4.metric(' Gross Margin',   f'{gross_margin:.1f}%')
    st.markdown('---')

    col1,col2 = st.columns(2)
    with col1:
        st.subheader(' Revenue by Year')
        fig = px.bar(revenue_df.groupby('year')['amount'].sum().reset_index(),
                     x='year',y='amount',labels={'amount':'Revenue (USD)','year':'Year'},
                     color_discrete_sequence=['#2196F3'])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader(' Revenue by Region')
        fig = px.pie(revenue_df.groupby('region')['amount'].sum().reset_index(),names='region',values='amount')
        st.plotly_chart(fig, use_container_width=True)

    col1,col2 = st.columns(2)
    with col1:
        st.subheader(' Revenue by Product')
        fig = px.bar(revenue_df.groupby('product')['amount'].sum().reset_index(),
                     x='product',y='amount',color='product',labels={'amount':'Revenue (USD)','product':'Product'})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader(' Expense Breakdown')
        fig = px.pie(expense_df.groupby('category')['amount'].sum().reset_index(),names='category',values='amount')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(' Monthly Revenue Trend')
    fig = px.line(revenue_df.groupby('month')['amount'].sum().reset_index().sort_values('month'),
                  x='month',y='amount',labels={'amount':'Revenue (USD)','month':'Month'})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(' Budget vs Actual by Department')
    bva_s = bva_df.groupby('department')[['budget_amount','actual_amount']].sum().reset_index()
    fig = px.bar(bva_s,x='department',y=['budget_amount','actual_amount'],barmode='group',
                 labels={'value':'Amount (USD)','department':'Department'})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(' Payroll by Department')
    fig = px.bar(payroll_df.groupby('department')['gross_monthly_pay'].sum().reset_index(),
                 x='department',y='gross_monthly_pay',color='department',
                 labels={'gross_monthly_pay':'Total Payroll (USD)','department':'Department'})
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════
# PAGE 2 — FINOPS DASHBOARD
# ════════════════════════════════════════════════════════════════
elif page == 'FinOps Dashboard':
    try:
        st.title(' FinOps Dashboard')
        st.markdown('### Traxovian Inc. — Cost Intelligence & Anomaly Detection')
        st.markdown('---')

        exp = load_table('expenses')
        bva = load_table('budget_vs_actual')

        st.subheader(' Feature 1 — Budget Anomaly Detection')
        st.markdown('Flags departments spending more than 20% above their 3-month rolling average.')

        monthly = exp.groupby(['department','month'])['amount'].sum().reset_index()
        monthly.columns = ['department','month','total_spend']
        monthly = monthly.sort_values(['department','month'])
        monthly['avg_3month'] = (monthly.groupby('department')['total_spend']
                                 .transform(lambda x: x.rolling(3,min_periods=1).mean()).round(2))
        monthly['over_by_pct'] = ((monthly['total_spend']-monthly['avg_3month'])/monthly['avg_3month']*100).round(2)

        def anomaly_label(x):
            if x>40: return ' Critical'
            elif x>20: return ' Warning'
            else: return ' Normal'

        monthly['anomaly_status'] = monthly['over_by_pct'].apply(anomaly_label)
        flagged = monthly[monthly['anomaly_status']!=' Normal'].sort_values('over_by_pct',ascending=False)

        col1,col2,col3 = st.columns(3)
        col1.metric(' Critical',      len(flagged[flagged['anomaly_status']==' Critical']))
        col2.metric(' Warnings',      len(flagged[flagged['anomaly_status']==' Warning']))
        col3.metric(' Total Flagged', len(flagged))

        if flagged.empty: st.success(' No anomalies. All departments within normal range.')
        else: st.dataframe(flagged,use_container_width=True)

        st.markdown('---')
        dept = st.selectbox(' Department spend trend:',sorted(monthly['department'].unique()),key='anomaly_dept')
        fig  = px.line(monthly[monthly['department']==dept],x='month',y=['total_spend','avg_3month'],
                       title=f'{dept} — Spend vs 3-Month Average',labels={'value':'USD','month':'Month'},
                       color_discrete_map={'total_spend':'#EF5350','avg_3month':'#42A5F5'})
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('---')

        st.subheader(' Feature 2 — Variance Tracker')
        monthly_var = (bva.groupby(['department','period','year'])
                       .agg(budget=('budget_amount','sum'),actual=('actual_amount','sum'),variance=('variance','sum'))
                       .reset_index())
        monthly_var['variance_pct'] = (monthly_var['variance']/monthly_var['budget']*100).round(2)
        monthly_var = monthly_var.sort_values(['department','period'])
        monthly_var['cumulative_variance'] = monthly_var.groupby('department')['variance'].cumsum().round(2)

        dept_summary = (monthly_var.groupby('department')
                        .agg(avg_variance_pct=('variance_pct','mean'),total_variance=('variance','sum'),
                             months_over_budget=('variance',lambda x:(x>0).sum()))
                        .reset_index())
        first_over = (monthly_var[monthly_var['variance']>0].groupby('department')['period'].min().reset_index())
        first_over.columns = ['department','first_overrun_month']
        dept_summary = dept_summary.merge(first_over,on='department',how='left')

        def risk_label(x):
            if x>15: return ' High Risk'
            elif x>5: return ' Medium Risk'
            else: return ' On Track'

        dept_summary['risk_level']       = dept_summary['avg_variance_pct'].apply(risk_label)
        dept_summary['avg_variance_pct'] = dept_summary['avg_variance_pct'].round(2)
        dept_summary['total_variance']   = dept_summary['total_variance'].round(2)

        col1,col2,col3 = st.columns(3)
        col1.metric(' High Risk',   len(dept_summary[dept_summary['risk_level']==' High Risk']))
        col2.metric(' Medium Risk', len(dept_summary[dept_summary['risk_level']==' Medium Risk']))
        col3.metric(' On Track',    len(dept_summary[dept_summary['risk_level']==' On Track']))
        st.dataframe(dept_summary,use_container_width=True)

        st.markdown('---')
        dept2    = st.selectbox(' Department variance:',sorted(monthly_var['department'].unique()),key='variance_dept')
        dept_var = monthly_var[monthly_var['department']==dept2]
        fig  = px.bar(dept_var,x='period',y='variance',title=f'{dept2} — Monthly Variance',
                      labels={'variance':'Variance (USD)','period':'Month'},
                      color='variance',color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig,use_container_width=True)
        fig2 = px.line(dept_var,x='period',y='cumulative_variance',
                       title=f'{dept2} — Cumulative Variance Over Time',
                       labels={'cumulative_variance':'Total Variance (USD)','period':'Month'})
        st.plotly_chart(fig2,use_container_width=True)
        st.markdown('---')

        st.subheader(' Feature 3 — AI Cost Optimizer')
        if st.button(' Run AI Cost Analysis',type='primary'):
            with st.spinner('Analyzing...'):
                from groq import Groq
                load_dotenv()
                api_key = os.getenv('GROQ_API_KEY')
                client = Groq(api_key=api_key)
                engine = create_engine('sqlite:///db/finsight.db')
                top_exp   = (exp.groupby(['category','sub_category'])['amount'].sum().reset_index()
                             .sort_values('amount',ascending=False).head(8))
                flagged_d = flagged[['department','month','total_spend','over_by_pct','anomaly_status']].head(5)
                high_risk = dept_summary[dept_summary['risk_level']!=' On Track'][
                    ['department','avg_variance_pct','total_variance','risk_level']]
                prompt = (f"FinOps consultant for Traxovian Inc.\nTOP 8 EXPENSES:\n{top_exp.to_string(index=False)}\n"
                          f"ANOMALIES:\n{flagged_d.to_string(index=False)}\nOVER BUDGET:\n{high_risk.to_string(index=False)}\n"
                          f"Give 5 specific recommendations. Format: RECOMMENDATION [n]: [title] / TARGETS: / ACTION: / SAVING: / PRIORITY:")
                result = client.chat.completions.create(
                    model='llama-3.3-70b-versatile',temperature=0.3,max_tokens=1000,
                    messages=[{'role':'system','content':'You are a FinOps consultant.'},
                               {'role':'user','content':prompt}])
                st.session_state['finops_recs'] = result.choices[0].message.content.strip()

        if 'finops_recs' in st.session_state:
            st.markdown('###  Recommendations:')
            for rec in st.session_state['finops_recs'].split('RECOMMENDATION'):
                if rec.strip() and len(rec.strip())>10:
                    st.info(f'**RECOMMENDATION** {rec.strip()}')

    except Exception as e:
        st.error(f'FinOps error: {e}')

# ════════════════════════════════════════════════════════════════
# PAGE 3 — AI COST GOVERNANCE
# ════════════════════════════════════════════════════════════════

elif page == 'AI Cost Governance':
    try:
        import plotly.graph_objects as go
        from itertools import product as iproduct

        st.title(' AI Cost Governance')
        st.markdown('### Who is spending what on AI — and what is it delivering?')
        st.markdown(
            '**Period:** Jan 2024 – Dec 2025 &nbsp;|&nbsp; '
            '**Employees:** 43 &nbsp;|&nbsp; '
            '**Products:** TraxCore (ERP) · TraxCRM · TraxAnalytics &nbsp;|&nbsp; '
            '**Providers:** Anthropic · OpenAI · Google · Groq'
        )
        st.markdown('---')

        sessions = load_table('ai_sessions')
        daily    = load_table('ai_daily_cost')
        alerts   = load_table('ai_alerts')

        total_cost   = sessions['cost_usd'].sum()
        total_sess   = len(sessions)
        days_elapsed = sessions['date'].nunique()
        burn_rate    = total_cost / days_elapsed if days_elapsed > 0 else 0
        projected    = burn_rate * 30

        col1,col2,col3,col4 = st.columns(4)
        col1.metric(' Total AI Spend (2yr)', f'${total_cost:,.2f}')
        col2.metric(' Avg Daily Burn Rate',  f'${burn_rate:,.2f}/day')
        col3.metric(' Projected Monthly',    f'${projected:,.2f}')
        col4.metric(' Total Sessions',       f'{total_sess:,}')
        st.markdown('---')

        # ── ALERTS ────────────────────────────────────────────
        if not alerts.empty:
            st.subheader(' Budget Alert History — 2024 to 2025')
            col1,col2,col3,col4 = st.columns(4)
            col1.metric(' Budget Exceeded', len(alerts[alerts['alert_type']==' Budget Exceeded']))
            col2.metric(' Critical (90%)',  len(alerts[alerts['alert_type']==' Critical (90%)']))
            col3.metric(' Warning (70%)',   len(alerts[alerts['alert_type']==' Warning (70%)']))
            col4.metric(' Halfway (50%)',   len(alerts[alerts['alert_type']==' Halfway (50%)']))

            for _, a in alerts.sort_values('date', ascending=False).head(8).iterrows():
                msg = (f"**{a['alert_type']}** — **{a['department']}** · {a['month']} · "
                       f"${a['cumulative_cost']:,.2f} of ${a['monthly_budget']:,.0f} ({a['actual_pct']:.0f}%)")
                if '🚨' in a['alert_type'] or '🔴' in a['alert_type']: st.error(msg)
                elif '🟡' in a['alert_type']: st.warning(msg)
                else: st.info(msg)


        # ── Monthly trend ────
        st.subheader(' Monthly AI Spend by Department')

        monthly = sessions.groupby(['month','department'])['cost_usd'].sum().reset_index()
        monthly = monthly.sort_values('month')

        # Show Engineering separately
        col1, col2 = st.columns(2)
        with col1:
            eng_m = monthly[monthly['department']=='Engineering']
            fig = px.line(eng_m, x='month', y='cost_usd',
                          title='Engineering — Monthly AI Spend',
                          labels={'cost_usd':'Cost (USD)','month':'Month'},
                          color_discrete_sequence=['#F44336'])
            fig.update_traces(line_width=2)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            non_eng = monthly[monthly['department']!='Engineering']
            fig = px.line(non_eng, x='month', y='cost_usd', color='department',
                          title='All Other Departments — Monthly AI Spend',
                          labels={'cost_usd':'Cost (USD)','month':'Month'})
            st.plotly_chart(fig, use_container_width=True)

        # Single chart with log scale — shows all depts together
        st.markdown('**All departments on the same chart (log scale so all are visible):**')
        fig = px.line(monthly, x='month', y='cost_usd', color='department',
                      title='Monthly AI Cost — All Departments (Log Scale)',
                      labels={'cost_usd':'Cost USD (log)','month':'Month'},
                      log_y=True)
        st.plotly_chart(fig, use_container_width=True)

        # ── Dept spend ────────────
        st.subheader(' AI Spend by Department')

        dept_cost = sessions.groupby('department')['cost_usd'].sum().reset_index().sort_values('cost_usd', ascending=False)
        dept_cost['pct_of_total'] = (dept_cost['cost_usd']/dept_cost['cost_usd'].sum()*100).round(1)

        # Two charts: full picture + non-engineering zoom
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(dept_cost, x='department', y='cost_usd',
                         title='All Departments — Total AI Cost (2yr)',
                         labels={'cost_usd':'Cost (USD)','department':'Department'},
                         color='department',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            non_eng_cost = dept_cost[dept_cost['department']!='Engineering']
            fig = px.bar(non_eng_cost, x='department', y='cost_usd',
                         title='Non-Engineering Departments — AI Cost Zoom',
                         labels={'cost_usd':'Cost (USD)','department':'Department'},
                         color='department',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        # Pie with all depts
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(dept_cost, names='department', values='cost_usd',
                         title='AI Spend Share by Department',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Budget context table
            budget_map = {'Engineering':400,'Sales':90,'Marketing':80,'Finance':100,
                          'Operations':70,'HR':50,'Support':60,'Legal':50}
            dept_cost['monthly_budget']    = dept_cost['department'].map(budget_map)
            dept_cost['monthly_avg_spend'] = (dept_cost['cost_usd']/24).round(2)
            dept_cost['vs_budget']         = dept_cost.apply(
                lambda r: ' Over'   if r['monthly_avg_spend'] > r['monthly_budget']
                     else ' Near'   if r['monthly_avg_spend'] > r['monthly_budget']*0.7
                     else ' Within', axis=1)
            st.markdown('**Monthly avg vs budget:**')
            st.dataframe(
                dept_cost[['department','cost_usd','pct_of_total','monthly_avg_spend','monthly_budget','vs_budget']].rename(
                    columns={'cost_usd':'Total Cost','pct_of_total':'% Share',
                              'monthly_avg_spend':'Avg Monthly','monthly_budget':'Budget/Month',
                              'vs_budget':'Status'}),
                use_container_width=True)
        st.markdown('---')

        # ── PROVIDER SPLIT ────────────────────────────────────
        st.subheader(' Spend by AI Provider')
        prov = sessions.groupby('provider')['cost_usd'].sum().reset_index()
        prov['pct'] = (prov['cost_usd']/prov['cost_usd'].sum()*100).round(1)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(prov, names='provider', values='cost_usd',
                         title='Provider Cost Share',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(prov.sort_values('cost_usd', ascending=False),
                         x='provider', y='cost_usd',
                         title='Total Spend per Provider',
                         labels={'cost_usd':'Cost (USD)','provider':'Provider'},
                         color='provider',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        # ── YoY ───────────────────────────────────────────────
        st.subheader(' Year-over-Year AI Spend')
        yoy = sessions.groupby('year')['cost_usd'].sum().reset_index()
        col1, col2 = st.columns(2)
        for i, (_, row) in enumerate(yoy.iterrows()):
            [col1,col2][i].metric(f" {int(row['year'])} Total", f"${row['cost_usd']:,.2f}")

        monthly_total = sessions.groupby('month')['cost_usd'].sum().reset_index().sort_values('month')
        fig = px.bar(monthly_total, x='month', y='cost_usd',
                     title='Monthly AI Spend — Q3 2024 is where adoption accelerated',
                     labels={'cost_usd':'Cost (USD)','month':'Month'},
                     color_discrete_sequence=['#42A5F5'])
        fig.add_vrect(x0='2024-06', x1='2024-09', fillcolor='orange', opacity=0.15,
                      annotation_text='Q3 2024 Ramp-Up', annotation_position='top left')
        st.plotly_chart(fig, use_container_width=True)
        st.caption('Traxovian ran a small AI pilot Jan–Jun 2024. Adoption accelerated in Q3 2024. 2025 = full adoption across all departments.')
        st.markdown('---')

        # ── PRODUCT ───────────────────────────────────────────
        st.subheader(' AI Spend by Traxovian Product')
        prod_cost = sessions.groupby('product')['cost_usd'].sum().reset_index().sort_values('cost_usd',ascending=False)
        col1,col2,col3 = st.columns(3)
        for i,(_,row) in enumerate(prod_cost.iterrows()):
            [col1,col2,col3][i].metric(f" {row['product']}", f"${row['cost_usd']:,.2f}")
        fig = px.bar(prod_cost, x='product', y='cost_usd',
                     labels={'cost_usd':'Cost (USD)','product':'Product'}, color='product',
                     color_discrete_map={'TraxCore (ERP)':'#1E88E5','TraxCRM':'#43A047','TraxAnalytics':'#FB8C00'})
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('---')

        # ── MODEL COST ────────────────────────────────────────
        st.subheader(' Cost by AI Model')
        release_dates = {
            'claude-3-haiku':'Mar 2024','claude-3-5-sonnet':'Jun 2024','claude-3-5-haiku':'Nov 2024',
            'claude-3-7-sonnet':'Feb 2025','claude-sonnet-4':'May 2025','claude-opus-4':'Jul 2025',
            'gpt-4-turbo':'Apr 2024','gpt-4o':'May 2024','gpt-4o-mini':'Jul 2024',
            'gpt-o1-mini':'Sep 2024','gpt-o3-mini':'Jan 2025','gemini-1.5-flash':'May 2024',
            'gemini-1.5-pro':'May 2024','gemini-2.0-flash':'Feb 2025','gemini-2.0-pro':'Mar 2025',
            'llama-3-70b':'Apr 2024','llama-3.1-70b':'Jul 2024','llama-3.3-70b':'Dec 2024','mixtral-8x7b':'Apr 2024',
        }
        model_cost = sessions.groupby('model')['cost_usd'].sum().reset_index().sort_values('cost_usd',ascending=False)
        model_cost['label'] = model_cost['model'] + '  [' + model_cost['model'].map(release_dates).fillna('?') + ']'
        fig = px.bar(model_cost, x='cost_usd', y='label', orientation='h',
                     labels={'cost_usd':'Total Cost (USD)','label':'Model'},
                     color='cost_usd', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('---')

        # ── BUDGET vs ACTUAL monthly per dept ─────────────────
        st.subheader(' Budget vs Actual — Monthly View per Department')
        st.markdown('Red bars = month where actual spend exceeded budget. Green = under budget. Blue dashed line = monthly budget.')

        dept_filter = st.selectbox(
            'Select department:',
            sorted(sessions['department'].unique()),
            key='bva_dept'
        )
        budget_map_full = {'Engineering':400,'Sales':90,'Marketing':80,'Finance':100,
                           'Operations':70,'HR':50,'Support':60,'Legal':50}
        monthly_dept = (sessions[sessions['department']==dept_filter]
                        .groupby('month')['cost_usd'].sum().reset_index())
        monthly_dept.columns = ['month','actual_cost']
        monthly_dept['budget_cost'] = budget_map_full.get(dept_filter, 100)
        monthly_dept['variance']    = (monthly_dept['actual_cost'] - monthly_dept['budget_cost']).round(2)
        monthly_dept = monthly_dept.sort_values('month')

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Actual Cost', x=monthly_dept['month'], y=monthly_dept['actual_cost'],
            marker_color=['#F44336' if v>0 else '#4CAF50' for v in monthly_dept['variance']]
        ))
        fig.add_trace(go.Scatter(
            name='Budget Cost', x=monthly_dept['month'], y=monthly_dept['budget_cost'],
            mode='lines', line=dict(color='#1E88E5', width=2, dash='dash')
        ))
        fig.update_layout(
            title=f'{dept_filter} — Monthly AI Spend vs Budget',
            xaxis_title='Month', yaxis_title='USD'
        )
        st.plotly_chart(fig, use_container_width=True)

        over_months  = len(monthly_dept[monthly_dept['variance']>0])
        under_months = len(monthly_dept[monthly_dept['variance']<=0])
        col1,col2,col3 = st.columns(3)
        col1.metric(' Months Over Budget',  over_months)
        col2.metric(' Months Under Budget', under_months)
        col3.metric(' Total Variance',      f"${monthly_dept['variance'].sum():,.2f}")
        st.markdown('---')

        # ── Alert Heatmap ────────────
        if not alerts.empty:
            st.subheader(' AI Spend Alert Timeline')
            st.markdown(
                'Each cell = one department in one month. '
                '**Darker = more severe alert. White/light = clean month (no alert).**'
            )

            all_months = sorted(sessions['month'].unique())
            all_depts  = sorted(sessions['department'].unique())

            alerts['alert_type'] = alerts['alert_type'].str.strip()

            severity_map_local = {
                ' Budget Exceeded':   4,
                ' Critical (90%)':   3,
                ' Warning (70%)':    2,
                ' Halfway (50%)':    1,
            }
            alerts['severity_score'] = alerts['alert_type'].map(severity_map_local).fillna(0)
            alert_max = alerts.groupby(['department','month'])['severity_score'].max().reset_index()

            # Build complete grid
            grid_rows = []
            for dept, month in iproduct(all_depts, all_months):
                match = alert_max[(alert_max['department']==dept) & (alert_max['month']==month)]
                score = int(match['severity_score'].values[0]) if len(match)>0 else 0
                grid_rows.append({'Department':dept,'Month':month,'Score':score})

            grid_df = pd.DataFrame(grid_rows)
            pivot   = grid_df.pivot(index='Department', columns='Month', values='Score')
            pivot   = pivot.fillna(0).astype(int)

            fig = px.imshow(
                pivot,
                color_continuous_scale=[
                    [0.00, '#E8F5E9'],   # 0 = clean — light green
                    [0.25, '#FFF9C4'],   # 1 = halfway — light yellow
                    [0.50, '#FFE0B2'],   # 2 = warning — light orange
                    [0.75, '#FFCDD2'],   # 3 = critical — light red
                    [1.00, '#B71C1C'],   # 4 = exceeded — dark red
                ],
                zmin=0, zmax=4,
                title='AI Spend Alert Heatmap — Jan 2024 to Dec 2025',
                labels=dict(x='Month', y='Department', color='Alert Level'),
                aspect='auto'
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                coloraxis_colorbar=dict(
                    tickvals=[0,1,2,3,4],
                    ticktext=[' Clean',' Halfway',' Warning',' Critical',' Exceeded']
                )
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                ' Light green = clean, no alert · '
                ' Yellow = halfway through budget · '
                ' Orange = warning at 70% · '
                ' Pink/red = critical at 90% · '
                ' Dark red = budget exceeded'
            )
        st.markdown('---')

        # ── TOP 15 SPENDERS ───────────────────────────────────
        st.subheader(' Top 15 AI Spenders — All Departments')
        top_emp = (
            sessions.groupby(['employee_id','department'])
            .agg(total_cost=('cost_usd','sum'), sessions=('session_id','count'),
                 total_tokens=('total_tokens','sum'))
            .reset_index().sort_values('total_cost', ascending=False).head(15)
        )
        top_emp['total_cost']   = top_emp['total_cost'].round(2)
        top_emp['total_tokens'] = top_emp['total_tokens'].apply(lambda x: f'{x:,}')
        st.dataframe(top_emp, use_container_width=True)
        st.markdown('---')

        # ── TASK COST ─────────────────────────────────────────
        st.subheader(' Task Cost Analysis')
        task = (sessions.groupby('task_type')
                .agg(total_cost=('cost_usd','sum'), sessions=('session_id','count'),
                     avg_cost=('cost_usd','mean'), total_tokens=('total_tokens','sum'))
                .reset_index().sort_values('total_cost', ascending=False))
        task['avg_cost'] = task['avg_cost'].round(4)

        col1,col2 = st.columns(2)
        with col1:
            fig = px.bar(task.head(15), x='total_cost', y='task_type', orientation='h',
                         title='Top 15 Tasks by Total Cost',
                         labels={'total_cost':'Total Cost (USD)','task_type':'Task'},
                         color='total_cost', color_continuous_scale='Oranges')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(task, x='sessions', y='avg_cost', size='total_cost', color='task_type',
                             title='Sessions vs Avg Cost per Session',
                             labels={'sessions':'Sessions','avg_cost':'Avg Cost/Session (USD)'},
                             hover_data=['total_cost','total_tokens'])
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('---')

        # ── PERFORMANCE ───────────────────────────────────────
        st.subheader(' AI Usage Performance — Sessions per Employee')
        st.markdown(
            ' **High Performance** = efficient heavy users · '
            ' **High Productivity** = moderate effective users · '
            ' **Low Performance** = high usage, low output · '
            ' **Low Productivity** = minimal or inefficient'
        )
        perf_dept = (sessions.groupby(['department','performance'])
                     .agg(employees=('employee_id','nunique'),
                          sessions=('session_id','count'), cost=('cost_usd','sum'))
                     .reset_index())
        fig = px.bar(perf_dept, x='department', y='employees', color='performance', barmode='stack',
                     title='Performance Classification by Department',
                     labels={'employees':'Employees','department':'Department'},
                     color_discrete_map={
                         'High Performance':'#4CAF50','High Productivity':'#8BC34A',
                         'Low Performance':'#FF9800','Low Productivity':'#F44336'},
                     category_orders={'performance':
                         ['High Performance','High Productivity','Low Performance','Low Productivity']})
        st.plotly_chart(fig, use_container_width=True)

        col1,col2 = st.columns(2)
        with col1:
            perf_total = sessions['performance'].value_counts().reset_index()
            perf_total.columns = ['Performance','Sessions']
            fig = px.pie(perf_total, names='Performance', values='Sessions',
                         title='Overall Performance Distribution',
                         color='Performance',
                         color_discrete_map={
                             'High Performance':'#4CAF50','High Productivity':'#8BC34A',
                             'Low Performance':'#FF9800','Low Productivity':'#F44336'})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            sess_per = sessions.groupby(['department','employee_id']).size().reset_index(name='sessions')
            sess_dept = sess_per.groupby('department')['sessions'].mean().reset_index()
            sess_dept.columns = ['department','avg_sessions']
            sess_dept['avg_sessions'] = sess_dept['avg_sessions'].round(1)
            fig = px.bar(sess_dept.sort_values('avg_sessions', ascending=False),
                         x='department', y='avg_sessions',
                         title='Avg Sessions per Employee by Department',
                         labels={'avg_sessions':'Avg Sessions','department':'Department'},
                         color='avg_sessions', color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('---')
        eng_cost = sessions[sessions['department']=='Engineering']['cost_usd'].sum()


    except Exception as e:
        import traceback
        st.error(f'AI Governance error: {e}')
        st.code(traceback.format_exc())
        st.info('Copy this error and share it for a fix.')

# ════════════════════════════════════════════════════════════════
# PAGE 4 — ASK AI
# ════════════════════════════════════════════════════════════════
elif page == 'Ask AI':
    st.title(' Ask FinSight AI')
    st.markdown('Ask anything about Traxovian — financials, FinOps, AI costs, payroll, or budget.')
    st.markdown('---')

    FULL_SCHEMA = """
You are a financial and AI cost analyst for Traxovian Inc., a mid-market SaaS company.
SQLite database tables:

FINANCIAL:
1. revenue (transaction_id, date, month, quarter, year, type, sub_type, product, plan,
            customer_id, sales_rep, region, department, amount, currency, payment_terms, payment_status, churn_risk)
2. expenses (transaction_id, date, month, quarter, year, type, category, sub_category,
             vendor_id, department, amount, currency, approval_status, payment_method)
3. payroll (payroll_id, date, month, quarter, year, employee_id, department, role,
            employment_type, base_salary_annual, gross_monthly_pay, bonus, taxes_withheld, net_pay, currency, status)
4. budget_vs_actual (budget_id, period, quarter, year, department, category,
                     budget_amount, actual_amount, variance, variance_pct, status)

AI GOVERNANCE:
5. ai_sessions (session_id, timestamp, date, month, quarter, year, week,
                employee_id, department, product, ai_tool, model, provider,
                task_type, input_tokens, output_tokens, total_tokens, cost_usd, performance)
6. ai_daily_cost (date, month, quarter, year, department, daily_cost, sessions,
                  tokens_used, monthly_budget, cumulative_monthly_cost, budget_used_pct)
7. ai_alerts (alert_id, date, month, quarter, year, department, alert_type,
              threshold_pct, actual_pct, cumulative_cost, monthly_budget, overspend, severity)

RULES:
- Return ONLY valid SQLite SQL. No markdown, backticks, or explanation.
- revenue → revenue table. expenses → expenses. AI spend → ai_sessions or ai_daily_cost.
- alerts → ai_alerts. payroll → payroll. budget variance → budget_vs_actual.
- Dates: WHERE year = X or WHERE month = 'YYYY-MM'
"""

    from groq import Groq
    load_dotenv()
    api_key = os.getenv('GROQ_API_KEY')
    client = Groq(api_key=api_key)

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    st.markdown('**Click a question to try it:**')
    examples = [
        "What was total revenue in 2023?",
        "Which region generated most revenue?",
        "Top 3 expense categories?",
        "Highest payroll department?",
        "Engineering AI spend in 2025?",
        "Which AI model cost the most?",
        "Budget alerts triggered in 2025?",
        "Department with most AI sessions?",
        "Total AI spend 2024 vs 2025?",
        "Which product made most revenue?",
        "Departments that exceeded AI budget?",
        "Total budget variance all departments?",
    ]
    cols = st.columns(4)
    for i,ex in enumerate(examples):
        if cols[i%4].button(ex,key=f'btn_{i}'): st.session_state['prefill']=ex
    st.markdown('---')

    user_input = st.text_input(' Your question:',
                                value=st.session_state.get('prefill',''),
                                placeholder='e.g. How much did Engineering spend on AI in 2025?')

    if st.button(' Ask FinSight AI',type='primary'):
        if user_input.strip()=='':
            st.warning('Please type a question first.')
        else:
            with st.spinner('Thinking...'):
                try:
                    sql_resp  = client.chat.completions.create(
                        model='llama-3.3-70b-versatile',temperature=0,max_tokens=500,
                        messages=[{'role':'system','content':FULL_SCHEMA},
                                   {'role':'user','content':f'SQL query for: {user_input}'}])
                    sql_query = sql_resp.choices[0].message.content.strip()
                    result_df = pd.read_sql(sql_query,engine)
                    exp_resp  = client.chat.completions.create(
                        model='llama-3.3-70b-versatile',temperature=0.3,max_tokens=300,
                        messages=[{'role':'user','content':
                            f'User asked: "{user_input}"\nData: {result_df.to_string()}\n'
                            f'2-3 sentence plain English summary as Traxovian financial analyst.'}])
                    output = {'question':user_input,'sql':sql_query,'result':result_df,
                              'explanation':exp_resp.choices[0].message.content.strip(),'error':None}
                except Exception as e:
                    output = {'question':user_input,'sql':'','result':None,'explanation':None,'error':str(e)}
            st.session_state.chat_history.insert(0,output)
            if 'prefill' in st.session_state: del st.session_state['prefill']

    for item in st.session_state.chat_history:
        with st.container():
            st.markdown(f'** Question:** {item["question"]}')
            if item['error']: st.error(f' {item["error"]}')
            else:
                st.code(item['sql'],language='sql')
                st.success(item['explanation'])
                if item['result'] is not None and not item['result'].empty:
                    st.dataframe(item['result'],use_container_width=True)
            st.markdown('---')

    if not st.session_state.chat_history:
        st.info(' Click a question or type your own.')

# ════════════════════════════════════════════════════════════════
# PAGE 5 — RAW DATA
# ════════════════════════════════════════════════════════════════
elif page == 'Raw Data':
    st.title(' Raw Data Explorer')
    st.markdown('Browse all data powering FinSight AI.')
    st.markdown('---')

    TABLE_INFO = {
        'revenue':         ' 15,000 revenue transactions',
        'expenses':        ' 15,000 expense transactions',
        'payroll':         ' 12,000 payroll records',
        'budget_vs_actual':' 9,216 budget vs actual records',
        'ai_sessions':     ' 75,000+ AI usage sessions — Jan 2024 to Dec 2025',
        'ai_daily_cost':   ' Daily cost per department',
        'ai_alerts':       ' Budget alert history — 2024 to 2025',
    }

    table_choice = st.selectbox('Select a table:',list(TABLE_INFO.keys()))
    st.info(TABLE_INFO[table_choice])
    df = load_table(table_choice)

    col1,col2,col3 = st.columns(3)
    col1.metric('Total Rows',f'{len(df):,}')
    col2.metric('Total Columns',f'{len(df.columns)}')
    col3.metric('Date Range',f"{df['year'].min()} – {df['year'].max()}" if 'year' in df.columns else 'N/A')
    st.markdown('---')

    if 'year' in df.columns:
        sel_year = st.selectbox('Filter by year:',['All']+sorted([str(y) for y in df['year'].unique()]))
        if sel_year!='All': df=df[df['year']==int(sel_year)]

    if 'department' in df.columns:
        sel_dept = st.selectbox('Filter by department:',['All']+sorted(df['department'].unique().tolist()))
        if sel_dept!='All': df=df[df['department']==sel_dept]

    st.dataframe(df,use_container_width=True,height=500)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(' Download as CSV',data=csv,
                        file_name=f'traxovian_{table_choice}.csv',mime='text/csv')