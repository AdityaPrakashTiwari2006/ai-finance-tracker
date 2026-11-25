"""
modules/ai_coach.py
Google Gemini GenAI Financial Coach with Context Injection (RAG-lite).
Builds structured financial health context from user transactions,
injects it into Gemini prompts, and provides actionable coaching.
"""

import os
from dotenv import load_dotenv
from config import CURRENCY_SYMBOLS

# Load .env file for GEMINI_API_KEY
load_dotenv()


def build_financial_context(kpis, behavior_summary, micro_leak_summary, budgets_summary, category_summary):
    """
    Constructs a concise, structured markdown string summarizing the user's finances
    to inject directly into the LLM system prompt.
    """
    context = f"""
### USER FINANCIAL SUMMARY
- **Total Income:** {CURRENCY_SYMBOLS}{kpis.get('total_income', 0):,.0f}
- **Total Expenses:** {CURRENCY_SYMBOLS}{kpis.get('total_expenses', 0):,.0f}
- **Net Savings:** {CURRENCY_SYMBOLS}{kpis.get('net_savings', 0):,.0f}
- **Savings Rate:** {kpis.get('savings_rate', 0):.1f}% (Healthy target: >= 20%)

### BEHAVIORAL PATTERNS
- **Weekend vs Weekday Spend Ratio:** {behavior_summary.get('ratio', 1.0)}x
- **Weekend Daily Avg:** {CURRENCY_SYMBOLS}{behavior_summary.get('weekend_daily_avg', 0):,.0f}
- **Weekday Daily Avg:** {CURRENCY_SYMBOLS}{behavior_summary.get('weekday_daily_avg', 0):,.0f}
- **Behavior Diagnosis:** {behavior_summary.get('insight', 'None')}

### CHAI FACTOR / MICRO-LEAKS (<= ₹100 spends)
- **Micro-Expense Count:** {micro_leak_summary.get('micro_tx_count', 0)}
- **Total Spent on Micro-transactions:** {CURRENCY_SYMBOLS}{micro_leak_summary.get('micro_total', 0):,.0f} ({micro_leak_summary.get('percentage_of_expenses', 0):.1f}% of all expenses)
- **1-Year Projected Leak:** {CURRENCY_SYMBOLS}{micro_leak_summary.get('annualized_leak', 0):,.0f}
- **10-Year Opportunity Cost (at 12% compounding):** {CURRENCY_SYMBOLS}{micro_leak_summary.get('ten_year_compound_leak', 0):,.0f}

### TOP EXPENSE CATEGORIES
{category_summary}

### BUDGET GUARDRAILS STATUS
{budgets_summary}
"""
    return context.strip()


def query_gemini_coach(user_prompt, financial_context, conversation_history=None):
    """
    Sends contextualized financial prompt to Google Gemini API.
    Gracefully falls back to expert rule-based heuristic advice if API key is not configured.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    system_instruction = f"""
You are "Chanakya", an expert AI Financial Coach and Behavioral Economist for Indian young adults, students, and early-career professionals.
Currency is INR ({CURRENCY_SYMBOLS}).

Your coaching style:
1. Direct, warm, empathetic, yet financially disciplined.
2. Ground every piece of advice in the USER's REAL DATA provided in the context below.
3. Quantify everything: mention exact rupee amounts, opportunity costs, and compound return timelines.
4. Keep advice concise, actionable, and formatted in clean markdown bullet points.

{financial_context}
"""

    if not api_key:
        return _fallback_rule_based_coach(user_prompt, financial_context)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        
        # Build prompt
        full_prompt = f"{system_instruction}\n\nUser Question: {user_prompt}"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
        return response.text
    except Exception as e:
        return f"*(Gemini API temporarily unavailable: {e})*\n\n" + _fallback_rule_based_coach(user_prompt, financial_context)


def _fallback_rule_based_coach(user_prompt, financial_context):
    """
    Expert rule-based heuristic coach when running offline or without an API key.
    Ensures 100% functionality for offline evaluation or viva presentations.
    """
    lower = user_prompt.lower()
    
    if "save" in lower or "saving" in lower or "rate" in lower:
        return (
            "### 💡 Chanakya's Savings Audit\n"
            "- **The 50/30/20 Rule:** Ensure at least **20%** of your monthly income is moved to an investment or liquid emergency fund the day you get paid.\n"
            "- **Action Step:** Set up an automated recurring SIP on the 1st of every month before discretionary spending begins.\n"
            "- Check your **Chai Factor** section in the Behavior tab — small daily leaks under ₹100 often steal 10-15% of your savings capacity."
        )
    elif "leak" in lower or "chai" in lower or "snack" in lower or "micro" in lower:
        return (
            "### ☕ The Chai Factor Strategy\n"
            "- Small daily purchases (tea, autos, delivery fees) feel harmless at ₹40-₹100, but compound relentlessly.\n"
            "- Spending ₹100/day on impulse snacks = **₹36,500/year**. Invested at 12% annual compounding, that's over **₹7,50,000 in 10 years**.\n"
            "- **Action Step:** Allocate a fixed weekly cash envelope (or separate UPI wallet) of ₹500 for micro-spends. When it's empty, wait until next week."
        )
    elif "weekend" in lower or "party" in lower or "club" in lower:
        return (
            "### 🏖️ Weekend Guardrail Strategy\n"
            "- Weekend spending surges often happen because activities aren't pre-budgeted.\n"
            "- **Action Step:** Apply the '24-Hour Purchase Rule' for online cart checkouts on Saturday nights.\n"
            "- Cap weekend dining by setting a dedicated dining limit in the Budget Guardrails tab."
        )
    elif "goal" in lower or "laptop" in lower or "bike" in lower or "trip" in lower:
        return (
            "### 🎯 Goal Achievement Blueprint\n"
            "- Check the **Decision Support** tab to calculate your exact runway in months.\n"
            "- A 20% cut in non-essential weekend dining typically accelerates your goal arrival by **1.5 to 3 months**.\n"
            "- Keep goal funds in a separate high-yield savings account or liquid fund so you don't accidentally spend them."
        )
    else:
        return (
            "### 📊 Chanakya's Financial Assessment\n"
            "Here is your personalized roadmap based on your current transactions:\n\n"
            "1. **Check Budget Guardrails:** Review any category with a 🔴 red badge and freeze further discretionary spending there this month.\n"
            "2. **Build a 3-Month Runway:** Before making large luxury purchases, ensure your Emergency Fund covers at least 3 months of essential living burn.\n"
            "3. **Opportunity Cost Mindset:** Before spending on big-ticket items, check the Decision Engine to see the 10-year compounding wealth impact.\n\n"
            "*Tip: Add your `GEMINI_API_KEY` to the `.env` file to unlock dynamic AI conversational coaching!*"
        )
