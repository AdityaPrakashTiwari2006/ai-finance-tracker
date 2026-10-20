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
    if df is None or df.empty:
        return pd.DataFrame(columns=['category', 'amount', 'percentage'])
    expenses = df[df['type'] == 'Expense']
    if expenses.empty:
        return pd.DataFrame(columns=['category', 'amount', 'percentage'])
    summary = expenses.groupby('category')['amount'].sum().reset_index()
    summary = summary.sort_values('amount', ascending=False)
    grand_total = summary['amount'].sum()
    summary['percentage'] = (summary['amount'] / grand_total * 100) if grand_total > 0 else 0.0
    return summary

def plot_category_donut(df):
    summary = get_category_summary(df)
    if summary.empty:
        return px.pie(title="No expense data for selected period")
    fig = px.pie(summary, values='amount', names='category', hole=0.4, title='Spending by Category')
    return fig

def plot_income_vs_expense_category(df):
    if df is None or df.empty:
        return px.bar(title="No transaction data for selected period")
    total = df.groupby('type')['amount'].sum().reset_index()
    fig = px.bar(total, x='type', y='amount', color='type', title='Income Vs Expenses',
               labels={'amount': f"Amount ({CURRENCY_SYMBOLS})", 'type': 'Type'})
    return fig

def plot_monthly_trend(df):
    if df is None or df.empty:
        return px.line(title="No expense data recorded")

    expenses = df[df["type"] == "Expense"].copy()
    if expenses.empty:
        return px.line(title="No expense data recorded")
        
    expenses["date"] = pd.to_datetime(expenses["date"])
    expenses["year_month"] = expenses["date"].dt.strftime("%Y-%m")
    monthly = expenses.groupby("year_month")["amount"].sum().reset_index()
    monthly = monthly.sort_values("year_month")
    
    fig = px.line(
        monthly, x="year_month", y="amount",
        title="Monthly Spending Trendline", markers=True,
        labels={"year_month": "Month", "amount": f"Total Spent ({CURRENCY_SYMBOLS})"},
    )
    return fig
