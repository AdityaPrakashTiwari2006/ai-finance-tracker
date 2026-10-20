import streamlit as st 
from datetime import date, datetime
import pandas as pd
from config import CURRENCY_SYMBOLS, EXPENSE_CATEGORIES, INCOME_CATEGORIES, TRANSACTION_TYPES, DEFAULT_BUDGETS
from modules.analytics import (
    calculate_kpis,
    get_category_summary,
    plot_category_donut,
    plot_income_vs_expense_category,
    plot_monthly_trend,
)
from database.db_manager import (
    init_db,
    add_transaction,
    load_transactions_df,
    delete_transaction,
    preload_seed_data,
    update_transaction,
)

st.set_page_config(
    page_title='Finance Tracker',
    page_icon='💰',
    layout='wide'
)

init_db()
preload_seed_data()
df = load_transactions_df()
if not df.empty:
    df['date'] = pd.to_datetime(df['date'])

st.title('💰 Personal Finance Tracker')

tab_transaction,tab_dashboard=st.tabs(['🗳️Transaction','📊Dashboard'])
with tab_transaction:
    col_form, col_data = st.columns([1, 2], border=True)

    with col_form:
        st.subheader("Add Transaction")
        tx_type = st.radio('Types', TRANSACTION_TYPES, horizontal=True)
        if tx_type == 'Expense':
            tx_category = st.selectbox('Categories', EXPENSE_CATEGORIES)
        else:
            tx_category = st.selectbox('Categories', INCOME_CATEGORIES)
                
        with st.form('Transaction_form', clear_on_submit=True):
            tx_date = st.date_input('Date', value=date.today())
            tx_amount = st.number_input(f"Amount ({CURRENCY_SYMBOLS})", min_value=0.01, step=1.0)
            tx_note = st.text_input("Note (optional)", placeholder="eg. swiggy dinner")
            submitted = st.form_submit_button(f"🗳️ Save {tx_type}")
        
            if submitted:
                add_transaction(tx_date, tx_amount, tx_category, tx_type, tx_note)
                st.session_state["saved_msg"] = f"✅ {tx_type} of {CURRENCY_SYMBOLS}{tx_amount:,.2f} saved!"
                st.rerun()

    if "saved_msg" in st.session_state:
        st.success(st.session_state["saved_msg"])
        del st.session_state["saved_msg"] 
    
    with col_data:
        st.subheader('Transaction history')
    
        if df.empty:
            st.info('No transaction yet. Start your first transaction from left 👈')
        else:
            # Display the formatted dataframe
            display_df = df.copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            st.dataframe(
                display_df[['id', 'date', 'type', 'category', 'amount', 'note']],
                width='stretch',
                hide_index=True
            )

    st.markdown('-----')
    del_col1, del_col2 = st.columns([3, 1])
    with del_col1:
        del_id = st.number_input("Enter Transaction Id to delete:", min_value=1, step=1)
    with del_col2:
        st.write("")
        st.write("")
        if st.button("Delete"):
            delete_transaction(int(del_id))
            st.warning(f'Deleted Transaction #{int(del_id)}')
            st.rerun()

    st.markdown('---')
    st.title("Edit transaction 🖋️") 
    edit_id = st.number_input("Enter transaction ID to edit:", min_value=1, step=1, key='edit_id') 
    if edit_id:
        existing = df[df['id'] == edit_id]
        if not existing.empty:
            row = existing.iloc[0] 
            with st.form('Edit Transaction', clear_on_submit=True):
                new_date = st.date_input("Date", value=pd.to_datetime(row["date"]))
                new_type = st.radio('Type', TRANSACTION_TYPES, index=TRANSACTION_TYPES.index(row['type']), horizontal=True)
                new_category = st.selectbox('Categories', EXPENSE_CATEGORIES if new_type == 'Expense' else INCOME_CATEGORIES)
                new_amount = st.number_input('Amount(₹)', min_value=0.01, value=float(row['amount']))
                new_note = st.text_input('Note', value=str(row['note']))
                update_btn = st.form_submit_button('Update transaction 🗳️')
                if update_btn:
                    update_transaction(edit_id, new_date, new_amount, new_category, new_type, new_note)
                    st.session_state['msg'] = f'Transaction #{edit_id} updated!'
                    st.rerun() 
            if "msg" in st.session_state:
                st.success(st.session_state["msg"])
                del st.session_state["msg"] 
        else:
            st.warning(f'No transaction found with #{edit_id}')

    st.markdown('---')
    
with tab_dashboard:
    # 1. Always load data and convert dates right away
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])

    # 2. Time-period filtering
    time_filter = st.selectbox('📆 Time period', ['All Time', 'This month', 'Last month'])
    today = date.today()

    if not df.empty:
        if time_filter == "This month":
            filtered_df = df[(df['date'].dt.month == today.month) & (df['date'].dt.year == today.year)]
        elif time_filter == "Last month":
            last_m = today.month - 1 if today.month > 1 else 12
            last_y = today.year if today.month > 1 else today.year - 1
            filtered_df = df[(df['date'].dt.month == last_m) & (df['date'].dt.year == last_y)]
        else:
            filtered_df = df


    # 3. KPI Metrics
    if not df.empty:
        kpis = calculate_kpis(filtered_df)
        m1, m2, m3, m4 = st.columns(4, border=True)
        m1.metric('Total Income', f"{CURRENCY_SYMBOLS}{kpis['total_income']:,.0f}")
        m2.metric('Total Expense', f"{CURRENCY_SYMBOLS}{kpis['total_expenses']:,.0f}")
        m3.metric('Net Saving', f"{CURRENCY_SYMBOLS}{kpis['net_savings']:,.0f}")
        m4.metric('Saving Rate', f"{kpis['savings_rate']:,.1f}%")
        st.markdown("---")

    # Visualizations & Category breakdown
    summary = get_category_summary(filtered_df)
    st.subheader('Category Breakdown')
    st.dataframe(summary, use_container_width=True, hide_index=True)

    chart1, chart2 = st.columns(2)
    with chart1:
        st.plotly_chart(plot_category_donut(filtered_df), use_container_width=True)
    with chart2:
        st.plotly_chart(plot_income_vs_expense_category(filtered_df), use_container_width=True)

    st.subheader('💳 Budget Guardrails')    
    if not filtered_df.empty:
        cat_summary = get_category_summary(filtered_df)
        for category, budget in DEFAULT_BUDGETS.items():
            match = cat_summary[cat_summary['category'] == category]
            spent = match['amount'].values[0] if not match.empty else 0.0
            ratio = spent / budget
        
            col_name, col_bar, col_status = st.columns([2, 4, 2])
            col_name.write(f"**{category}**")
            col_bar.progress(min(ratio, 1.0))
        
            if ratio >= 1.0:
                col_status.error(f"{CURRENCY_SYMBOLS}{spent:,.0f} / {CURRENCY_SYMBOLS}{budget:,.0f} 🔴")
            elif ratio >= 0.75:
                col_status.warning(f"{CURRENCY_SYMBOLS}{spent:,.0f} / {CURRENCY_SYMBOLS}{budget:,.0f} 🟡")
            else:
                col_status.success(f"{CURRENCY_SYMBOLS}{spent:,.0f} / {CURRENCY_SYMBOLS}{budget:,.0f} 🟢")

    st.markdown('---')
    st.plotly_chart(plot_monthly_trend(df), use_container_width=True)





