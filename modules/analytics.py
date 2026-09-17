import pandas as pd
import plotly.express as px
from config import CURRENCY_SYMBOLS

def calculate_kpis(df):
    if df is None or df.empty:
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_savings": 0.0,
            "savings_rate": 0.0,
        }

    income_df = df[df['type'] == 'Income']
    expense_df = df[df['type'] == 'Expense']

    total_income = float(income_df['amount'].sum()) if not income_df.empty else 0.0
    total_expenses = float(expense_df['amount'].sum()) if not expense_df.empty else 0.0

    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100.0) if total_income > 0 else 0.0

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": net_savings,
        "savings_rate": savings_rate,
    }
def get_category_summary(df):
    expenses=df[df['type']=='Expense']
    summary=expenses.groupby('category')['amount'].sum().reset_index()
    summary=summary.sort_values('amount',ascending=False)
    grand_total=summary['amount'].sum()
    summary['percentage']=(summary['amount']/grand_total *100)
    return summary