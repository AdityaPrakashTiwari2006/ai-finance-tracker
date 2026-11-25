"""
modules/behavior.py
Behavioral Economics & Financial Habit Analytics Engine.
Detects:
1. Weekend vs Weekday spending patterns & surge detection.
2. The 'Chai Factor' / Micro-expense leaks (transactions <= ₹100).
3. Recurring fixed expenses & subscription commitments.
"""

import pandas as pd
from config import CURRENCY_SYMBOLS


def analyze_weekend_vs_weekday(df):
    """
    Compares weekend (Sat/Sun) vs weekday (Mon-Fri) daily average spending.
    Diagnoses lifestyle spending distribution.
    """
    if df is None or df.empty:
        return {
            "weekend_total": 0.0,
            "weekday_total": 0.0,
            "weekend_daily_avg": 0.0,
            "weekday_daily_avg": 0.0,
            "ratio": 0.0,
            "insight": "No transaction data available.",
        }

    expenses = df[df["type"] == "Expense"].copy()
    if expenses.empty:
        return {
            "weekend_total": 0.0,
            "weekday_total": 0.0,
            "weekend_daily_avg": 0.0,
            "weekday_daily_avg": 0.0,
            "ratio": 0.0,
            "insight": "No expenses recorded yet.",
        }

    expenses["date"] = pd.to_datetime(expenses["date"])
    # 5 = Saturday, 6 = Sunday
    expenses["is_weekend"] = expenses["date"].dt.weekday >= 5

    weekend_df = expenses[expenses["is_weekend"]]
    weekday_df = expenses[~expenses["is_weekend"]]

    weekend_total = float(weekend_df["amount"].sum())
    weekday_total = float(weekday_df["amount"].sum())

    weekend_days = max(weekend_df["date"].dt.date.nunique(), 1) if not weekend_df.empty else 0
    weekday_days = max(weekday_df["date"].dt.date.nunique(), 1) if not weekday_df.empty else 0

    weekend_daily_avg = (weekend_total / weekend_days) if weekend_days > 0 else 0.0
    weekday_daily_avg = (weekday_total / weekday_days) if weekday_days > 0 else 0.0

    ratio = (weekend_daily_avg / weekday_daily_avg) if weekday_daily_avg > 0 else 0.0

    if ratio >= 1.3:
        insight = f"⚠️ Weekend Surge Detected: You spend {ratio:.1f}x more per day on weekends ({CURRENCY_SYMBOLS}{weekend_daily_avg:,.0f}/day vs {CURRENCY_SYMBOLS}{weekday_daily_avg:,.0f}/day)."
    elif 0 < ratio <= 0.7:
        insight = f"💼 Weekday-Driven Spend: Daily college/commute routines drive most expenses ({CURRENCY_SYMBOLS}{weekday_daily_avg:,.0f}/day vs {CURRENCY_SYMBOLS}{weekend_daily_avg:,.0f}/day on weekends)."
    elif ratio == 0.0 and weekend_total == 0:
        insight = "🌱 Frugal Weekends: Zero weekend expenses recorded in this period."
    else:
        insight = f"⚖️ Balanced Spender: Spending is well-distributed ({CURRENCY_SYMBOLS}{weekend_daily_avg:,.0f}/day on weekends, {CURRENCY_SYMBOLS}{weekday_daily_avg:,.0f}/day on weekdays)."

    return {
        "weekend_total": weekend_total,
        "weekday_total": weekday_total,
        "weekend_daily_avg": weekend_daily_avg,
        "weekday_daily_avg": weekday_daily_avg,
        "ratio": round(ratio, 2),
        "insight": insight,
    }


def detect_chai_factor(df, threshold=100.0):
    """
    Detects small repetitive discretionary expenses (<= ₹100),
    aka the 'Chai/Latte Factor', and projects the 1-year and 10-year compounding leak.
    """
    if df is None or df.empty:
        return {
            "micro_tx_count": 0,
            "micro_total": 0.0,
            "percentage_of_expenses": 0.0,
            "annualized_leak": 0.0,
            "ten_year_compound_leak": 0.0,
            "top_micro_notes": [],
            "insight": "No data to analyze micro-leaks.",
        }

    expenses = df[df["type"] == "Expense"].copy()
    if expenses.empty:
        return {
            "micro_tx_count": 0,
            "micro_total": 0.0,
            "percentage_of_expenses": 0.0,
            "annualized_leak": 0.0,
            "ten_year_compound_leak": 0.0,
            "top_micro_notes": [],
            "insight": "No expense transactions recorded.",
        }

    total_expense_sum = float(expenses["amount"].sum())
    micro_df = expenses[expenses["amount"] <= threshold].copy()

    if micro_df.empty:
        return {
            "micro_tx_count": 0,
            "micro_total": 0.0,
            "percentage_of_expenses": 0.0,
            "annualized_leak": 0.0,
            "ten_year_compound_leak": 0.0,
            "top_micro_notes": [],
            "insight": f"✅ Great discipline! No micro-transactions under {CURRENCY_SYMBOLS}{threshold:,.0f} detected.",
        }

    micro_count = len(micro_df)
    micro_total = float(micro_df["amount"].sum())
    pct = (micro_total / total_expense_sum * 100.0) if total_expense_sum > 0 else 0.0

    # Calculate date span to annualize accurately
    micro_df["date"] = pd.to_datetime(micro_df["date"])
    days_span = max((micro_df["date"].max() - micro_df["date"].min()).days + 1, 30)
    monthly_micro = (micro_total / days_span) * 30.0
    annualized = monthly_micro * 12.0

    # 10-Year Opportunity Cost compounding at 12% annual return (Nifty 50 historical avg)
    # Future Value of monthly SIP: P * [((1 + r)^n - 1) / r] * (1 + r)
    r_monthly = 0.12 / 12
    n_months = 120
    if monthly_micro > 0:
        ten_year_compound = monthly_micro * (((1 + r_monthly) ** n_months - 1) / r_monthly) * (1 + r_monthly)
    else:
        ten_year_compound = 0.0

    top_notes = (
        micro_df["note"]
        .fillna("Uncategorized")
        .value_counts()
        .head(5)
        .to_dict()
    )

    if pct >= 15.0:
        insight = f"🚨 High Chai Factor Alert! Small spends under {CURRENCY_SYMBOLS}{threshold:,.0f} represent {pct:.1f}% of your total expenses ({CURRENCY_SYMBOLS}{micro_total:,.0f}). That's ~{CURRENCY_SYMBOLS}{annualized:,.0f}/year leaking!"
    else:
        insight = f"☕ Controlled Chai Factor: Micro-expenses make up {pct:.1f}% of your budget ({CURRENCY_SYMBOLS}{micro_total:,.0f})."

    return {
        "micro_tx_count": micro_count,
        "micro_total": micro_total,
        "percentage_of_expenses": round(pct, 1),
        "annualized_leak": round(annualized, 0),
        "ten_year_compound_leak": round(ten_year_compound, 0),
        "top_micro_notes": top_notes,
        "insight": insight,
    }


def detect_recurring_subscriptions(df):
    """
    Detects repeated recurring expenses across notes or categories with identical amounts,
    identifying subscriptions like Netflix, Spotify, Gym, Rent, Wi-Fi.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["note", "category", "amount", "frequency", "total_paid"])

    expenses = df[df["type"] == "Expense"].copy()
    if expenses.empty:
        return pd.DataFrame(columns=["note", "category", "amount", "frequency", "total_paid"])

    # Group by cleaned note + category + amount to find repeating charges
    expenses["note_clean"] = (
        expenses["note"]
        .fillna("")
        .str.strip()
        .str.lower()
    )
    # Filter out empty notes
    named_expenses = expenses[expenses["note_clean"] != ""]

    if named_expenses.empty:
        # Fallback to category + amount recurrence
        grouped = expenses.groupby(["category", "amount"]).size().reset_index(name="frequency")
        recurring = grouped[grouped["frequency"] >= 2].copy()
        recurring["note"] = recurring["category"]
    else:
        grouped = (
            named_expenses.groupby(["note_clean", "category", "amount"])
            .size()
            .reset_index(name="frequency")
        )
        recurring = grouped[grouped["frequency"] >= 2].copy()
        recurring.rename(columns={"note_clean": "note"}, inplace=True)

    if recurring.empty:
        return pd.DataFrame(columns=["note", "category", "amount", "frequency", "total_paid"])

    recurring["total_paid"] = recurring["amount"] * recurring["frequency"]
    recurring = recurring.sort_values(by="total_paid", ascending=False).reset_index(drop=True)
    return recurring[["note", "category", "amount", "frequency", "total_paid"]]
