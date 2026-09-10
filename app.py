import streamlit as st 
from datetime import date 
from config import CURRENCY_SYMBOLS, EXPENSE_CATEGORIES, INCOME_CATEGORIES, TRANSACTION_TYPES
from database.db_manager import init_db,add_transaction, load_transactions_df, delete_transaction,preload_seed_data 

st.set_page_config(
    page_title='Finance Tracker',
    page_icon='💰',
    layout='wide'
)

init_db()
preload_seed_data()

st.title('💰 Personal Finance Tracker')

col_form,col_data=st.columns([1,2])

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