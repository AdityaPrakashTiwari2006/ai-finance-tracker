import streamlit as st
from datetime import date, datetime
import pandas as pd

from config import (
    CURRENCY_SYMBOLS,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    TRANSACTION_TYPES,
    DEFAULT_BUDGETS,
)
from database.db_manager import (
    init_db,
    add_transaction,
    load_transactions_df,
    delete_transaction,
    preload_seed_data,
    update_transaction,
)
from modules.analytics import (
    calculate_kpis,
    get_category_summary,
    plot_category_donut,
    plot_income_vs_expense_category,
    plot_monthly_trend,
)
from modules.behavior import (
    analyze_weekend_vs_weekday,
    detect_chai_factor,
    detect_recurring_subscriptions,
)
from modules.decision_support import (
    calculate_opportunity_cost,
    calculate_emergency_fund_health,
    plan_goal_timeline,
)
from modules.ml_categorizer import suggest_category
from modules.ai_coach import build_financial_context, query_gemini_coach

# Page Setup
st.set_page_config(
    page_title="AI Finance Tracker & Decision Engine",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database and seed records
init_db()
preload_seed_data()

# Load main dataframe & normalize date
df = load_transactions_df()
if not df.empty:
    df["date"] = pd.to_datetime(df["date"])

# ----------------- SIDEBAR: Time Filter & Fast Stats -----------------
with st.sidebar:
    st.title("💰 FinTrack AI")
    st.caption("Personal Finance Decision-Support System")
    st.markdown("---")

    time_filter = st.selectbox(
        "📆 Time Horizon",
        ["All Time", "This Month", "Last Month"],
        index=0,
    )

    today = date.today()
    if not df.empty:
        if time_filter == "This Month":
            filtered_df = df[(df["date"].dt.month == today.month) & (df["date"].dt.year == today.year)]
        elif time_filter == "Last Month":
            last_m = today.month - 1 if today.month > 1 else 12
            last_y = today.year if today.month > 1 else today.year - 1
            filtered_df = df[(df["date"].dt.month == last_m) & (df["date"].dt.year == last_y)]
        else:
            filtered_df = df
    else:
        filtered_df = df

    st.markdown("---")
    st.subheader("⚡ Quick Metric Snapshot")
    if not filtered_df.empty:
        kpis_side = calculate_kpis(filtered_df)
        st.metric("Net Savings", f"{CURRENCY_SYMBOLS}{kpis_side['net_savings']:,.0f}")
        st.metric("Savings Rate", f"{kpis_side['savings_rate']:,.1f}%")
    else:
        st.info("No records in this period.")

    st.markdown("---")
    st.caption("BCA Final Capstone Project\nDesigned with Python, SQLite, Pandas, Scikit-Learn & Gemini API")

# ----------------- TOP KPI BAR -----------------
st.title("Personal Finance & Behavioral Decision Engine")

if not df.empty:
    kpis = calculate_kpis(filtered_df)
    k1, k2, k3, k4 = st.columns(4, border=True)
    k1.metric("Total Income", f"{CURRENCY_SYMBOLS}{kpis['total_income']:,.0f}")
    k2.metric("Total Expenses", f"{CURRENCY_SYMBOLS}{kpis['total_expenses']:,.0f}")
    k3.metric("Net Savings", f"{CURRENCY_SYMBOLS}{kpis['net_savings']:,.0f}")
    k4.metric("Savings Rate", f"{kpis['savings_rate']:,.1f}%")
    st.markdown("---")

# ----------------- MAIN NAVIGATION TABS -----------------
tab_tx, tab_analytics, tab_behavior, tab_decision, tab_ai = st.tabs([
    "📥 Transactions",
    "📊 Analytics & Guardrails",
    "🧠 Behavioral Insights",
    "🎯 Decision Support",
    "🤖 Chanakya AI Coach",
])

# ==================== TAB 1: TRANSACTIONS (CRUD + ML Auto-Suggest) ====================
with tab_tx:
    col_form, col_data = st.columns([1, 2], border=True)

    with col_form:
        st.subheader("Add Transaction")
        tx_type = st.radio("Type", TRANSACTION_TYPES, horizontal=True)

        # Smart Note Input first to trigger ML auto-categorization
        tx_note = st.text_input("Note / Merchant Description", placeholder="e.g. Swiggy dinner, Uber cab, Dmart grocery")

        # ML Auto-Suggestion
        suggested_cat = None
        if tx_note.strip() and tx_type == "Expense":
            suggested_cat = suggest_category(tx_note)
            if suggested_cat in EXPENSE_CATEGORIES:
                st.caption(f"🤖 *ML Auto-detected Category:* **{suggested_cat}**")

        available_cats = EXPENSE_CATEGORIES if tx_type == "Expense" else INCOME_CATEGORIES
        default_index = 0
        if suggested_cat and suggested_cat in available_cats:
            default_index = available_cats.index(suggested_cat)

        tx_category = st.selectbox("Category", available_cats, index=default_index)

        with st.form("add_tx_form", clear_on_submit=True):
            tx_date = st.date_input("Date", value=date.today())
            tx_amount = st.number_input(f"Amount ({CURRENCY_SYMBOLS})", min_value=0.01, step=10.0)
            submitted = st.form_submit_button(f"🗳️ Save {tx_type}")

            if submitted:
                add_transaction(tx_date, tx_amount, tx_category, tx_type, tx_note)
                st.session_state["saved_msg"] = f"✅ {tx_type} of {CURRENCY_SYMBOLS}{tx_amount:,.2f} recorded!"
                st.rerun()

    if "saved_msg" in st.session_state:
        st.success(st.session_state["saved_msg"])
        del st.session_state["saved_msg"]

    with col_data:
        st.subheader("Transaction History")
        if df.empty:
            st.info("No transactions logged yet. Add your first record on the left! 👈")
        else:
            display_df = df.copy()
            display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(
                display_df[["id", "date", "type", "category", "amount", "note"]],
                width="stretch",
                hide_index=True,
            )

            st.markdown("---")
            d1, d2 = st.columns([3, 1])
            with d1:
                del_id = st.number_input("Transaction ID to delete:", min_value=1, step=1)
            with d2:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete", type="secondary"):
                    delete_transaction(int(del_id))
                    st.warning(f"Deleted Transaction #{int(del_id)}")
                    st.rerun()

    # Edit Transaction Section
    with st.expander("🖋️ Edit Existing Transaction"):
        edit_id = st.number_input("Enter Transaction ID to update:", min_value=1, step=1, key="edit_box")
        if edit_id:
            existing = df[df["id"] == edit_id]
            if not existing.empty:
                row = existing.iloc[0]
                with st.form("edit_form"):
                    e_date = st.date_input("Date", value=pd.to_datetime(row["date"]))
                    e_type = st.radio("Type", TRANSACTION_TYPES, index=TRANSACTION_TYPES.index(row["type"]), horizontal=True)
                    e_cats = EXPENSE_CATEGORIES if e_type == "Expense" else INCOME_CATEGORIES
                    curr_cat_idx = e_cats.index(row["category"]) if row["category"] in e_cats else 0
                    e_cat = st.selectbox("Category", e_cats, index=curr_cat_idx)
                    e_amount = st.number_input(f"Amount ({CURRENCY_SYMBOLS})", min_value=0.01, value=float(row["amount"]))
                    e_note = st.text_input("Note", value=str(row["note"]))
                    if st.form_submit_button("Update Transaction"):
                        update_transaction(edit_id, e_date, e_amount, e_cat, e_type, e_note)
                        st.session_state["edit_msg"] = f"Transaction #{edit_id} updated!"
                        st.rerun()
            else:
                st.warning(f"No transaction with ID #{edit_id}")

    if "edit_msg" in st.session_state:
        st.success(st.session_state["edit_msg"])
        del st.session_state["edit_msg"]


# ==================== TAB 2: ANALYTICS & GUARDRAILS ====================
with tab_analytics:
    st.subheader(f"📊 Spending Analytics & Budget Guardrails ({time_filter})")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_category_donut(filtered_df), width="stretch")
    with c2:
        st.plotly_chart(plot_income_vs_expense_category(filtered_df), width="stretch")

    st.markdown("---")
    st.subheader("💳 Category Budget Guardrails")
    st.caption("Active threshold alerts comparing current spending against monthly safe limits.")

    if not filtered_df.empty:
        cat_sum = get_category_summary(filtered_df)
        for category, budget in DEFAULT_BUDGETS.items():
            match = cat_sum[cat_sum["category"] == category]
            spent = match["amount"].values[0] if not match.empty else 0.0
            ratio = spent / budget

            col_name, col_bar, col_status = st.columns([2, 4, 2])
            col_name.write(f"**{category}**")
            col_bar.progress(min(ratio, 1.0))

            if ratio >= 1.0:
                col_status.error(f"{CURRENCY_SYMBOLS}{spent:,.0f} / {CURRENCY_SYMBOLS}{budget:,.0f} ({ratio*100:.0f}%) 🔴")
            elif ratio >= 0.75:
                col_status.warning(f"{CURRENCY_SYMBOLS}{spent:,.0f} / {CURRENCY_SYMBOLS}{budget:,.0f} ({ratio*100:.0f}%) 🟡")
            else:
                col_status.success(f"{CURRENCY_SYMBOLS}{spent:,.0f} / {CURRENCY_SYMBOLS}{budget:,.0f} ({ratio*100:.0f}%) 🟢")

    st.markdown("---")
    st.subheader("📈 Multi-Month Historical Spending Trajectory")
    st.plotly_chart(plot_monthly_trend(df), width="stretch")


# ==================== TAB 3: BEHAVIORAL INSIGHTS ====================
with tab_behavior:
    st.subheader("🧠 Behavioral Intelligence & Money Leak Detection")
    st.caption("Identifies psychological spending patterns, micro-leaks, and hidden subscription commitments.")

    b1, b2 = st.columns(2, border=True)

    with b1:
        st.markdown("### 🏖️ Weekend vs Weekday Surge Analysis")
        weekend_res = analyze_weekend_vs_weekday(filtered_df)
        st.info(weekend_res["insight"])

        w_col1, w_col2, w_col3 = st.columns(3)
        w_col1.metric("Weekend Spend", f"{CURRENCY_SYMBOLS}{weekend_res['weekend_total']:,.0f}")
        w_col2.metric("Weekday Spend", f"{CURRENCY_SYMBOLS}{weekend_res['weekday_total']:,.0f}")
        w_col3.metric("Ratio", f"{weekend_res['ratio']}x")

        st.caption(
            f"Weekend Daily Avg: {CURRENCY_SYMBOLS}{weekend_res['weekend_daily_avg']:,.0f}/day | "
            f"Weekday Daily Avg: {CURRENCY_SYMBOLS}{weekend_res['weekday_daily_avg']:,.0f}/day"
        )

    with b2:
        st.markdown("### ☕ The 'Chai Factor' (Micro-Expense Leak)")
        chai_res = detect_chai_factor(filtered_df)
        st.warning(chai_res["insight"])

        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Total Leaked", f"{CURRENCY_SYMBOLS}{chai_res['micro_total']:,.0f}")
        m_col2.metric("% of Expenses", f"{chai_res['percentage_of_expenses']}%")
        m_col3.metric("10-Yr Compounded", f"{CURRENCY_SYMBOLS}{chai_res['ten_year_compound_leak']:,.0f}")

        st.caption(f"Estimated 1-Year Leak: {CURRENCY_SYMBOLS}{chai_res['annualized_leak']:,.0f} across {chai_res['micro_tx_count']} micro-transactions.")

    st.markdown("---")
    st.markdown("### 🔄 Recurring Commitments & Subscriptions")
    recurring_df = detect_recurring_subscriptions(df)
    if recurring_df.empty:
        st.info("No repeated subscription patterns detected yet.")
    else:
        st.dataframe(
            recurring_df,
            column_config={
                "note": "Subscription / Merchant",
                "category": "Category",
                "amount": f"Amount ({CURRENCY_SYMBOLS})",
                "frequency": "Occurrences Detected",
                "total_paid": f"Total Paid ({CURRENCY_SYMBOLS})",
            },
            width="stretch",
            hide_index=True,
        )


# ==================== TAB 4: DECISION SUPPORT ====================
with tab_decision:
    st.subheader("🎯 Mathematical Financial Decision Support")
    st.caption("Simulate big purchases, emergency fund runways, and target goal timelines before spending.")

    d_col1, d_col2 = st.columns(2, border=True)

    with d_col1:
        st.markdown("### 💎 10-Year Opportunity Cost Calculator")
        st.caption("Calculate the true future wealth lost when spending on a discretionary purchase today.")

        sim_price = st.number_input("Item Purchase Price (₹)", min_value=100.0, value=25000.0, step=1000.0)
        sim_years = st.slider("Investment Horizon (Years)", min_value=1, max_value=25, value=10)
        sim_cagr = st.slider("Expected Annual Return (Index Fund %)", min_value=6.0, max_value=18.0, value=12.0) / 100.0

        opp_res = calculate_opportunity_cost(sim_price, annual_return=sim_cagr, years=sim_years)

        st.metric(
            label=f"Future Value at {sim_years} Years",
            value=f"{CURRENCY_SYMBOLS}{opp_res['future_value']:,.0f}",
            delta=f"-{CURRENCY_SYMBOLS}{opp_res['wealth_lost']:,.0f} Opportunity Cost",
            delta_color="inverse",
        )
        st.write(
            f"💡 **Decision Rule:** Spending **{CURRENCY_SYMBOLS}{sim_price:,.0f}** today robs your future self of "
            f"**{CURRENCY_SYMBOLS}{opp_res['future_value']:,.0f}** ({opp_res['multiplier']}x of current price) if invested in a standard index fund."
        )

    with d_col2:
        st.markdown("### 🛡️ Emergency Fund Health Evaluator")
        st.caption("Measures your liquid survival buffer against monthly essential burn.")

        kpis_all = calculate_kpis(df)
        net_saved = max(kpis_all["net_savings"], 0.0)
        user_savings = st.number_input("Liquid Emergency Savings (₹)", min_value=0.0, value=float(net_saved), step=5000.0)

        fund_res = calculate_emergency_fund_health(df, liquid_savings=user_savings)

        ef1, ef2 = st.columns(2)
        ef1.metric("Runway", f"{fund_res['runway_months']} Months")
        ef2.metric("Health Score", f"{fund_res['health_score']} / 100")

        st.info(f"Status: **{fund_res['status']}**")
        st.write(
            f"- **Avg Monthly Burn:** {CURRENCY_SYMBOLS}{fund_res['avg_monthly_burn']:,.0f}/month\n"
            f"- **Recommended 6-Month Buffer:** {CURRENCY_SYMBOLS}{fund_res['recommended_fund']:,.0f}"
        )

    st.markdown("---")
    st.markdown("### 🚀 Goal Timeline Planner")
    g1, g2, g3 = st.columns(3)
    g_name = g1.text_input("Goal Name", value="MacBook Pro / Gaming Laptop")
    g_target = g2.number_input("Target Cost (₹)", min_value=1000.0, value=80000.0, step=5000.0)
    g_curr = g3.number_input("Already Saved (₹)", min_value=0.0, value=15000.0, step=5000.0)

    # Monthly capacity from net savings
    avg_monthly_savings = max(kpis_all["net_savings"] / max(len(df["date"].dt.month.unique()) if not df.empty else 1, 1), 2000.0)
    g_monthly = st.slider("Monthly Savings Dedicated to Goal (₹)", min_value=500.0, max_value=50000.0, value=float(min(avg_monthly_savings, 15000.0)), step=500.0)

    goal_plan = plan_goal_timeline(g_name, g_target, g_curr, g_monthly)
    st.success(goal_plan["status"])


# ==================== TAB 5: CHANAKYA AI FINANCIAL COACH ====================
with tab_ai:
    st.subheader("🤖 Chanakya AI Financial Coach")
    st.caption("AI reasoning powered by Google Gemini with your live transaction context injected.")

    # Prepare formatted context string
    cat_summary_table = get_category_summary(filtered_df).to_string(index=False) if not filtered_df.empty else "No expenses."
    budget_status_str = "\n".join([
        f"- {cat}: Budget {CURRENCY_SYMBOLS}{b:,.0f}" for cat, b in DEFAULT_BUDGETS.items()
    ])

    ai_context = build_financial_context(
        kpis=calculate_kpis(filtered_df),
        behavior_summary=analyze_weekend_vs_weekday(filtered_df),
        micro_leak_summary=detect_chai_factor(filtered_df),
        budgets_summary=budget_status_str,
        category_summary=cat_summary_table,
    )

    # Quick prompt buttons
    st.write("**Ask Chanakya quick questions or type your custom query below:**")
    qp1, qp2, qp3, qp4 = st.columns(4)
    quick_q = None
    if qp1.button("🔍 Audit My Savings Rate"):
        quick_q = "Audit my savings rate and tell me how to reach the 20% healthy threshold."
    if qp2.button("☕ How do I cut my Chai Factor?"):
        quick_q = "How do I plug my micro-spending leaks and chai factor without feeling miserable?"
    if qp3.button("🏖️ How to control Weekend Spend?"):
        quick_q = "Give me 3 strict behavioral rules to prevent weekend spending surges."
    if qp4.button("🎯 Can I afford a luxury purchase?"):
        quick_q = "Evaluate whether I can afford an impulse luxury purchase based on my emergency runway."

    # Chat history in session state
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {"role": "assistant", "content": "Namaste! I am Chanakya, your AI Financial Coach. Ask me anything about your spending habits, budget leaks, or savings goals!"}
        ]

    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask Chanakya a financial question...")
    prompt_to_send = quick_q or user_input

    if prompt_to_send:
        st.session_state["chat_messages"].append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user"):
            st.markdown(prompt_to_send)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your financial context with Chanakya AI..."):
                response_text = query_gemini_coach(prompt_to_send, ai_context)
                st.markdown(response_text)
                st.session_state["chat_messages"].append({"role": "assistant", "content": response_text})
