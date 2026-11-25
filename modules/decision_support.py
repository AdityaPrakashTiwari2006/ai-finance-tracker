"""
modules/decision_support.py
Mathematical Decision-Support Engine:
1. 10-Year Opportunity Cost Calculator (FV of one-time & recurring spending).
2. Emergency Fund Runway & Financial Health Score.
3. Goal Timeline Planner (Target date with scenario adjustments).
"""

import math
import pandas as pd
from config import CURRENCY_SYMBOLS


def calculate_opportunity_cost(amount, annual_return=0.12, years=10):
    """
    Computes the compound future value of spending an amount today
    instead of investing in index funds (default: 12% Nifty 50 historical CAGR).
    FV = PV * (1 + r)^t
    """
    if amount <= 0:
        return {
            "principal": 0.0,
            "future_value": 0.0,
            "wealth_lost": 0.0,
            "multiplier": 1.0,
        }

    future_val = amount * ((1 + annual_return) ** years)
    wealth_lost = future_val - amount
    multiplier = future_val / amount if amount > 0 else 1.0

    return {
        "principal": float(amount),
        "future_value": round(float(future_val), 2),
        "wealth_lost": round(float(wealth_lost), 2),
        "multiplier": round(float(multiplier), 1),
    }


def calculate_emergency_fund_health(df, liquid_savings=None):
    """
    Evaluates emergency fund runway against monthly essential burn rate.
    Standard rule: 3-6 months of essential living expenses.
    """
    if df is None or df.empty:
        return {
            "avg_monthly_burn": 0.0,
            "runway_months": 0.0,
            "health_score": 0,
            "status": "No data",
            "recommended_fund": 0.0,
        }

    expenses = df[df["type"] == "Expense"].copy()
    if expenses.empty:
        return {
            "avg_monthly_burn": 0.0,
            "runway_months": 0.0,
            "health_score": 100,
            "status": "No expenses recorded",
            "recommended_fund": 0.0,
        }

    total_expense = float(expenses["amount"].sum())
    # Estimate months in dataset
    expenses["date"] = pd.to_datetime(expenses["date"]) if "date" in expenses else None
    if expenses["date"] is not None and not expenses["date"].empty:
        days = max((expenses["date"].max() - expenses["date"].min()).days + 1, 30)
        months = max(days / 30.0, 1.0)
    else:
        months = 1.0

    monthly_burn = total_expense / months

    # If user provided savings, evaluate exact runway. Else compute from net savings in df.
    if liquid_savings is None:
        incomes = df[df["type"] == "Income"]
        total_income = float(incomes["amount"].sum()) if not incomes.empty else 0.0
        liquid_savings = max(total_income - total_expense, 0.0)

    recommended_fund = monthly_burn * 6.0
    runway_months = (liquid_savings / monthly_burn) if monthly_burn > 0 else 0.0

    # Score: 6+ months = 100, 3 months = 50, <1 month = 15
    if runway_months >= 6.0:
        score = 100
        status = "🛡️ Excellent (6+ Months Buffer)"
    elif runway_months >= 3.0:
        score = 70
        status = "⚠️ Moderate (3-5 Months Buffer)"
    elif runway_months >= 1.0:
        score = 40
        status = "🚨 Low (1-2 Months Buffer)"
    else:
        score = 15
        status = "🔥 Critical (<1 Month Buffer)"

    return {
        "avg_monthly_burn": round(monthly_burn, 0),
        "current_savings": round(liquid_savings, 0),
        "runway_months": round(runway_months, 1),
        "recommended_fund": round(recommended_fund, 0),
        "health_score": score,
        "status": status,
    }


def plan_goal_timeline(goal_name, target_amount, current_savings, monthly_savings_capacity):
    """
    Calculates timeline in months to achieve a specific financial goal (e.g. Laptop, Bike, Vacation).
    Also simulates 'frugal boost' (saving an extra 20% by cutting leaks).
    """
    remaining = max(target_amount - current_savings, 0.0)
    if remaining == 0:
        return {
            "months_needed": 0,
            "boosted_months": 0,
            "time_saved_months": 0,
            "status": f"🎉 Goal '{goal_name}' is already fully funded!",
        }

    if monthly_savings_capacity <= 0:
        return {
            "months_needed": float("inf"),
            "boosted_months": float("inf"),
            "time_saved_months": 0,
            "status": "⚠️ Monthly net savings is ₹0 or negative. Reduce expenses or increase income to fund this goal.",
        }

    months_standard = math.ceil(remaining / monthly_savings_capacity)
    boosted_capacity = monthly_savings_capacity * 1.20  # 20% extra saved by cutting leaks
    months_boosted = math.ceil(remaining / boosted_capacity)
    time_saved = max(months_standard - months_boosted, 0)

    status = (
        f"🎯 Standard pace: {months_standard} months ({CURRENCY_SYMBOLS}{monthly_savings_capacity:,.0f}/mo). "
        f"With a 20% leak cut ({CURRENCY_SYMBOLS}{boosted_capacity:,.0f}/mo), you reach it in {months_boosted} months ({time_saved} months faster)!"
    )

    return {
        "goal_name": goal_name,
        "target_amount": target_amount,
        "remaining": remaining,
        "months_needed": months_standard,
        "boosted_months": months_boosted,
        "time_saved_months": time_saved,
        "status": status,
    }
