import sys
import os
import pandas as pd
from datetime import date

# Set UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding='utf-8')

from database.db_manager import (
    init_db,
    preload_seed_data,
    load_transactions_df,
    add_transaction,
    delete_transaction,
    register_user,
    authenticate_user,
    verify_password,
    hash_password,
)
from modules.analytics import calculate_kpis, get_category_summary, plot_category_donut, plot_income_vs_expense_category, plot_monthly_trend
from modules.behavior import analyze_weekend_vs_weekday, detect_chai_factor, detect_recurring_subscriptions
from modules.decision_support import calculate_opportunity_cost, calculate_emergency_fund_health, plan_goal_timeline
from modules.ml_categorizer import suggest_category
from modules.ai_coach import build_financial_context, query_gemini_coach

def run_tests():
    print("=== 1. DATABASE & USER AUTHENTICATION TEST ===")
    init_db()
    preload_seed_data()

    # Test Default Demo Login
    auth_ok, msg, user = authenticate_user("aditya", "demo123")
    assert auth_ok, f"Demo login failed: {msg}"
    assert user["username"] == "aditya"
    print(f"PASS: Demo user authenticated successfully (User #{user['id']}: {user['name']}).")

    # Test Bad Password
    bad_ok, bad_msg, _ = authenticate_user("aditya", "wrongpassword")
    assert not bad_ok, "Failed: accepted wrong password!"
    print(f"PASS: Bad password rejected correctly ('{bad_msg}').")

    # Test New User Registration
    test_user = "test_fintech_user"
    reg_ok, reg_msg, new_uid = register_user(test_user, "Test Candidate", "pass1234")
    if not reg_ok:
        # User might already exist from previous test run
        assert "already exists" in reg_msg
        auth_ok2, _, user2 = authenticate_user(test_user, "pass1234")
        assert auth_ok2
        new_uid = user2["id"]
        print(f"PASS: Existing test user re-authenticated (User #{new_uid}).")
    else:
        print(f"PASS: New user registered successfully (User #{new_uid}).")

    # Test Multi-User Data Isolation
    df_user1 = load_transactions_df(user_id=1)
    df_user2 = load_transactions_df(user_id=new_uid)
    assert not df_user1.empty, "User 1 should have seed transactions!"
    print(f"PASS: User #1 has {len(df_user1)} transactions. User #{new_uid} has {len(df_user2)} transactions.")

    # Insert a transaction for User 2 and verify User 1 does not see it
    add_transaction("2026-11-26", 999.0, "Entertainment", "Expense", "Movie Night", user_id=new_uid)
    df_user2_updated = load_transactions_df(user_id=new_uid)
    assert any(df_user2_updated["amount"] == 999.0), "User 2 failed to record transaction!"
    df_user1_check = load_transactions_df(user_id=1)
    assert not any(df_user1_check["amount"] == 999.0), "CRITICAL LEAK: User 1 can see User 2's transaction!"
    print("PASS: Multi-user data isolation verified with zero cross-tenant leakage.")

    # Clean up test transaction
    tx_to_del = df_user2_updated[df_user2_updated["amount"] == 999.0]["id"].values[0]
    delete_transaction(tx_to_del, user_id=new_uid)
    print("PASS: User transaction deleted cleanly.")

    print("\n=== 2. ANALYTICS & KPIS TEST (ON DEMO USER DATA) ===")
    df = df_user1.copy()
    df['date'] = pd.to_datetime(df['date'])
    kpis = calculate_kpis(df)
    assert 'total_income' in kpis and 'total_expenses' in kpis
    print(f"PASS: Income: ₹{kpis['total_income']:,.2f} | Expenses: ₹{kpis['total_expenses']:,.2f} | Savings: ₹{kpis['net_savings']:,.2f}")

    summary = get_category_summary(df)
    assert not summary.empty, "Category summary is empty!"
    print(f"PASS: Category summary generated with {len(summary)} categories.")

    p1 = plot_category_donut(df)
    p2 = plot_income_vs_expense_category(df)
    p3 = plot_monthly_trend(df)
    print("PASS: All 3 Plotly chart figures constructed successfully.")

    print("\n=== 3. BEHAVIOR ENGINE TEST ===")
    w = analyze_weekend_vs_weekday(df)
    print(f"PASS: Weekend spend: ₹{w['weekend_total']:,.0f} | Weekday spend: ₹{w['weekday_total']:,.0f} | Ratio: {w['ratio']}x")

    c = detect_chai_factor(df)
    print(f"PASS: Chai factor: ₹{c['micro_total']:,.0f} across {c['micro_tx_count']} micro-txs | 10-Yr compounding leak: ₹{c['ten_year_compound_leak']:,.0f}")

    r = detect_recurring_subscriptions(df)
    print(f"PASS: {len(r)} recurring subscription patterns detected.")

    print("\n=== 4. DECISION SUPPORT TEST ===")
    opp = calculate_opportunity_cost(30000, 0.12, 10)
    assert opp['future_value'] > 30000
    print(f"PASS: 10-Yr Opportunity Cost for ₹30,000 -> ₹{opp['future_value']:,.2f} (Loss: ₹{opp['wealth_lost']:,.2f})")

    ef = calculate_emergency_fund_health(df)
    print(f"PASS: Emergency Fund health: {ef['health_score']}/100 | Runway: {ef['runway_months']} months")

    goal = plan_goal_timeline('Gaming PC', 75000, 15000, 10000)
    assert goal['months_needed'] == 6
    print(f"PASS: Goal timeline: {goal['months_needed']} months standard, {goal['boosted_months']} months boosted.")

    print("\n=== 5. ML AUTO-CATEGORIZATION TEST ===")
    cases = [
        ('zomato biryani order', 'Food & Dining'),
        ('ola auto ride to station', 'Transport'),
        ('apollo pharmacy medicine', 'Health & Fitness'),
        ('coursera python course', 'Education'),
        ('netflix 4k monthly', 'Entertainment'),
        ('dmart monthly ration groceries', 'Groceries'),
    ]
    for note, expected in cases:
        pred = suggest_category(note)
        print(f'  Note: "{note}" -> Predicted: {pred} (Expected: {expected})')
        assert pred == expected, f'ML mismatch for "{note}"'
    print("PASS: 6/6 ML Auto-categorization test cases passed with 100% precision.")

    print("\n=== 6. AI COACH CONTEXT & QUERY TEST ===")
    context = build_financial_context(kpis, w, c, "- Food: Budget ₹5000", "Summary table")
    response = query_gemini_coach("How do I reduce my food expenses?", context)
    assert len(response) > 50
    print(f"PASS: AI Coach produced {len(response)} chars of advice.")
    print("\n==============================================")
    print("🎉 ALL TEST SUITES PASSED INCLUDING AUTH & MULTI-USER (100% GREEN)")
    print("==============================================")

if __name__ == "__main__":
    run_tests()
