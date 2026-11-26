import sys
import os
import io
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
    bulk_insert_transactions,
)
from modules.analytics import calculate_kpis, get_category_summary, plot_category_donut, plot_income_vs_expense_category, plot_monthly_trend
from modules.behavior import analyze_weekend_vs_weekday, detect_chai_factor, detect_recurring_subscriptions
from modules.decision_support import calculate_opportunity_cost, calculate_emergency_fund_health, plan_goal_timeline
from modules.ml_categorizer import suggest_category
from modules.ai_coach import build_financial_context, query_gemini_coach
from modules.statement_parser import parse_bank_statement, detect_statement_columns

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

    # Test Multi-User Data Isolation
    df_user1 = load_transactions_df(user_id=1)
    assert not df_user1.empty, "User 1 should have seed transactions!"
    print(f"PASS: User #1 has {len(df_user1)} transactions.")

    print("\n=== 2. BANK STATEMENT CSV PARSER & INGESTION TEST ===")
    # Create sample HDFC/SBI bank statement CSV format
    sample_csv = """Txn Date,Description,Withdrawal (Dr),Deposit (Cr),Balance
01/11/2026,UPI-SWIGGY-BANGALORE,450.00,,45550.00
02/11/2026,SALARY CREDIT NOV 2026,,65000.00,110550.00
03/11/2026,UBER RIDE MUMBAI,320.00,,110230.00
04/11/2026,NETFLIX COM MUMBAI,649.00,,109581.00
05/11/2026,ZEPTO GROCERY ORDER,890.00,,108691.00
"""
    success, p_msg, parsed_df = parse_bank_statement(sample_csv.encode("utf-8"))
    assert success, f"Failed parsing sample bank statement: {p_msg}"
    assert len(parsed_df) == 5, f"Expected 5 parsed rows, got {len(parsed_df)}"
    print(f"PASS: Bank statement parsed {len(parsed_df)} records: {p_msg}")

    # Verify ML auto-categorization occurred during statement import
    swiggy_cat = parsed_df[parsed_df["note"].str.contains("SWIGGY", case=False)]["category"].values[0]
    salary_cat = parsed_df[parsed_df["note"].str.contains("SALARY", case=False)]["category"].values[0]
    uber_cat = parsed_df[parsed_df["note"].str.contains("UBER", case=False)]["category"].values[0]

    assert swiggy_cat == "Food & Dining", f"Expected Food & Dining for Swiggy, got {swiggy_cat}"
    assert salary_cat == "Salary", f"Expected Salary, got {salary_cat}"
    assert uber_cat == "Transport", f"Expected Transport for Uber, got {uber_cat}"
    print(f"PASS: Statement ML Auto-categorization: Swiggy -> '{swiggy_cat}' | Salary -> '{salary_cat}' | Uber -> '{uber_cat}'")

    # Test Bulk Ingestion and Duplicate Avoidance
    test_user_id = 999
    records = parsed_df.to_dict(orient="records")
    inserted, skipped = bulk_insert_transactions(records, user_id=test_user_id, skip_duplicates=True)
    assert inserted == 5 and skipped == 0, f"Expected 5 inserted, 0 skipped. Got {inserted}, {skipped}"
    print(f"PASS: Bulk insert test: {inserted} inserted, {skipped} skipped.")

    # Re-insert identical batch to verify duplicate protection
    inserted2, skipped2 = bulk_insert_transactions(records, user_id=test_user_id, skip_duplicates=True)
    assert inserted2 == 0 and skipped2 == 5, f"Expected 0 inserted, 5 skipped. Got {inserted2}, {skipped2}"
    print(f"PASS: Duplicate prevention test: {inserted2} inserted, {skipped2} skipped (100% duplicate protection).")

    # Clean up test user records
    conn = init_db()
    from database.db_manager import get_connection
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE user_id = ?", (test_user_id,))
    conn.commit()
    conn.close()

    print("\n=== 3. ANALYTICS & KPIS TEST ===")
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

    print("\n=== 4. BEHAVIOR ENGINE TEST ===")
    w = analyze_weekend_vs_weekday(df)
    print(f"PASS: Weekend spend: ₹{w['weekend_total']:,.0f} | Weekday spend: ₹{w['weekday_total']:,.0f} | Ratio: {w['ratio']}x")

    c = detect_chai_factor(df)
    print(f"PASS: Chai factor: ₹{c['micro_total']:,.0f} across {c['micro_tx_count']} micro-txs | 10-Yr compounding leak: ₹{c['ten_year_compound_leak']:,.0f}")

    r = detect_recurring_subscriptions(df)
    print(f"PASS: {len(r)} recurring subscription patterns detected.")

    print("\n=== 5. DECISION SUPPORT TEST ===")
    opp = calculate_opportunity_cost(30000, 0.12, 10)
    assert opp['future_value'] > 30000
    print(f"PASS: 10-Yr Opportunity Cost for ₹30,000 -> ₹{opp['future_value']:,.2f} (Loss: ₹{opp['wealth_lost']:,.2f})")

    ef = calculate_emergency_fund_health(df)
    print(f"PASS: Emergency Fund health: {ef['health_score']}/100 | Runway: {ef['runway_months']} months")

    goal = plan_goal_timeline('Gaming PC', 75000, 15000, 10000)
    assert goal['months_needed'] == 6
    print(f"PASS: Goal timeline: {goal['months_needed']} months standard, {goal['boosted_months']} months boosted.")

    print("\n=== 6. ML AUTO-CATEGORIZATION TEST ===")
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

    print("\n=== 7. AI COACH CONTEXT & QUERY TEST ===")
    context = build_financial_context(kpis, w, c, "- Food: Budget ₹5000", "Summary table")
    response = query_gemini_coach("How do I reduce my food expenses?", context)
    assert len(response) > 50
    print(f"PASS: AI Coach produced {len(response)} chars of advice.")
    print("\n==============================================")
    print("🎉 ALL TEST SUITES PASSED (BANK CSV IMPORT + AUTH + ML + AI)")
    print("==============================================")

if __name__ == "__main__":
    run_tests()
