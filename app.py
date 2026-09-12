import streamlit as st 
from datetime import date 
import pandas as pd
from config import CURRENCY_SYMBOLS, EXPENSE_CATEGORIES, INCOME_CATEGORIES, TRANSACTION_TYPES
from modules.analytics import calculate_kpis
from database.db_manager import init_db,add_transaction, load_transactions_df,delete_transaction,preload_seed_data,update_transaction 

st.set_page_config(
    page_title='Finance Tracker',
    page_icon='💰',
    layout='wide'
)

init_db()
preload_seed_data()

st.title('💰 Personal Finance Tracker')

df=load_transactions_df()
if not df.empty:
    kpis=calculate_kpis(df)
    m1,m2,m3,m4=st.columns(4,border=True)
    m1.metric('Total Income', f"{CURRENCY_SYMBOLS}{kpis['total_income']:,.0f}")
    m2.metric('Total Expense', f"{CURRENCY_SYMBOLS}{kpis['total_expenses']:,.0f}")
    m3.metric('Net Saving', f"{CURRENCY_SYMBOLS}{kpis['net_savings']:,.0f}")
    m4.metric('Saving Rate', f"{kpis['savings_rate']:,.1f}%")
    st.markdown("---")

col_form,col_data=st.columns([1,2],border=True)


with col_form:
    st.subheader("Add Transaction")
    tx_type=st.radio('Types',TRANSACTION_TYPES,horizontal=True)
    if tx_type=='Expense':
        tx_category=st.selectbox('Categories',EXPENSE_CATEGORIES)
    else:
        tx_category=st.selectbox('Categories',INCOME_CATEGORIES)
                
    with st.form('Transaction_form',clear_on_submit=True):
        tx_date=st.date_input('Date',value=date.today())
        
        tx_amount=st.number_input(f"Amount ({CURRENCY_SYMBOLS}),",min_value=0.01,step=1.0)
        tx_note=st.text_input(f"Note(optional)",placeholder="eg.swiggy dinner")
        submitted=st.form_submit_button(f"🗳️ Save {tx_type}")
        
        if submitted:
            add_transaction(tx_date, tx_amount, tx_category, tx_type, tx_note)
            st.session_state["saved_msg"] = f"✅ {tx_type} of {CURRENCY_SYMBOLS}{tx_amount:,.2f} saved!"
            st.rerun()

if "saved_msg" in st.session_state:
    st.success(st.session_state["saved_msg"])
    del st.session_state["saved_msg"] 
    
with col_data:
    st.subheader('Transaction history')
    df=load_transactions_df()
    
    
    if df.empty:
        st.info('No transaction yet. Start your first transaction from left 👈')
    else:
        st.dataframe(df[['id','date','type','category','amount','note']],width='stretch',hide_index=True)

        st.markdown('-----')
        del_col1,del_col2=st.columns([3,1])
        with del_col1:
            del_id=st.number_input("Enter Transaction Id which need to be deleted:",min_value=1,step=1)
        with del_col2:
            st.write("")
            st.write("")
            if st.button("Delete"):
                delete_transaction(int(del_id))
                st.warning(f'Deleted Transaction #{int(del_id)}')
                st.rerun()
st.markdown('---')
st.title("Edit transaction 🖋️") 
edit_id=st.number_input("enter the transaction:",min_value=1,step=1,key='edit_id') 
if edit_id:
    existing=df[df['id']==edit_id]
    if not existing.empty:
        row=existing.iloc[0] 
        with st.form('Edit Transaction',clear_on_submit=True):
            new_date=st.date_input("Date",value=pd.to_datetime(row["date"]))
            new_type=st.radio('Type',TRANSACTION_TYPES,index=TRANSACTION_TYPES.index(row['type']),horizontal=True)
            new_category=st.selectbox('Categories',EXPENSE_CATEGORIES if new_type=='Expense' else INCOME_CATEGORIES)
            new_amount=st.number_input('Amount(₹)',min_value=0.01,value=float(row['amount']))
            new_note=st.text_input('Note',value=str(row['note']))
            update_btn=st.form_submit_button('Update transaction🗳️')
            if update_btn:
                update_transaction(edit_id,new_date,new_amount,new_category,new_type,new_note)
                st.session_state['msg']=f'Transaction #{edit_id} updated!'
                st.rerun() 
        if "msg" in st.session_state:
            st.success(st.session_state["msg"])
            del st.session_state["msg"] 
    else:
        st.warning(f'No transaction found with #{edit_id}')
