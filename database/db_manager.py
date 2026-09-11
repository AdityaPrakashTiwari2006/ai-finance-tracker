import sqlite3
import pandas as pd

DB_FILE="finance.db"

def get_connection():
    return sqlite3.connect(DB_FILE,check_same_thread=False)

def init_db():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        type TEXT NOT NULL,
        note TEXT)
    """)
    conn.commit()
    conn.close()
    
def add_transaction(date,amount,category,tx_type,note):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("""
                    INSERT INTO transactions(date,amount,category,type,note) VALUES(?,?,?,?,?)""",
                    (str(date),float(amount),category,tx_type,note))
    conn.commit()
    conn.close()
    
def load_transactions_df():
    conn=get_connection()
    df=pd.read_sql_query("Select * from transactions order by date desc",conn)
    conn.close()
    return df

def delete_transaction(transaction_id):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("Delete from transactions where id=?",(transaction_id,))
    conn.commit()
    conn.close()
    
def preload_seed_data():
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT count(*) FROM transactions")
    count=cursor.fetchone()[0]
    conn.close()
    
    if count==0:
        try:
            seed_df=pd.read_csv('data/seed_transactions.csv')
            for _,row in seed_df.iterrows():
                add_transaction(
                    row['date'],row['amount'],row['category'],row['type'],row['note']
                )
            print(f"Loaded {len(seed_df)} seed transactions")
        except FileNotFoundError:
            print("Seed file is not found.Starting with empty database.")
            
def update_transaction(id,date,amount,category,tx_type,note):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute(
        """UPDATE transactions set date=?,amount=?,category=?,type=?,note=? where id=?""",
        (str(date),float(amount),category,tx_type,note,id)
    )
    conn.commit()
    conn.close()
        