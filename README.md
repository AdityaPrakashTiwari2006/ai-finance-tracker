# 💰 FinTrack AI — Personal Finance Decision-Support System
> **An intelligent, behavioral financial decision engine built with Python, SQLite, Pandas, Scikit-Learn, Plotly, and Google Gemini LLM.**

---

## 📌 Executive Summary
Most personal finance applications act merely as passive digital ledgers—they tell users where their money went after it has already been spent. 

**FinTrack AI** is an active **Decision-Support System** that combines:
1. **Relational Database CRUD Layer:** SQLite data persistence with full transaction lifecycle management.
2. **Behavioral Analytics Engine:** Quantifies psychological spending patterns, including **Weekend Spending Surges**, the **"Chai Factor"** (compounding micro-expense leaks $\le$ ₹100), and automated subscription detection.
3. **Mathematical Decision-Support Engine:** Computes 10-year **Opportunity Cost** ($FV = PV \times (1 + r)^t$), evaluates **Emergency Fund Runway Health**, and simulates accelerated **Goal Timelines**.
4. **Machine Learning Classifier:** Scikit-Learn TF-IDF + Naive Bayes pipeline for automated transaction categorization.
5. **AI Financial Coach ("Chanakya"):** Google Gemini GenAI integrated with real-time user financial context injection.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   SQLite Database                      │
│            (finance.db + Seed Transactions)            │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                     Pandas Engine                      │
│            (Date parsing, Slicing, Aggregation)        │
└─────────┬────────────────┼─────────────────┬───────────┘
          │                │                 │
          ▼                ▼                 ▼
┌──────────────────┐┌──────────────┐┌────────────────────┐
│    Analytics     ││   Behavior   ││   ML Categorizer   │
│  (KPIs, Plotly,  ││(Weekend Surge││ (TF-IDF + Naive   │
│  Guardrails)     ││ Chai Factor) ││     Bayes)         │
└─────────┬────────┘└──────┬───────┘└─────────┬──────────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│                Decision Support Engine                 │
│         (Opportunity Cost, Runway, Goal Paths)         │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              Google Gemini AI Coach                    │
│      (Context-Injected Behavioral Financial Advisory)  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Interactive Streamlit Dashboard            │
│  (5 Multi-Tabs, Real-time Visualizations & Chat UI)    │
└────────────────────────────────────────────────────────┘
```

---

## ✨ Core Features & Technical Highlights

### 1. 📥 Transaction Hub (CRUD + ML Auto-Suggest)
* Full Create, Read, Update, and Delete operations over SQLite.
* **Auto-Categorization:** As the user types notes like `"Swiggy biryani"` or `"Uber to station"`, the built-in Scikit-Learn TF-IDF model automatically predicts and populates the category dropdown in real-time.

### 2. 📊 Spending Analytics & Budget Guardrails
* Interactive Plotly Donut and Income vs. Expense charts.
* Category Budget Guardrails featuring visual `st.progress` bars and color-coded status badges (🟢 Safe, 🟡 Warning, 🔴 Over Budget).
* Historical Multi-Month Trendline charting long-term trajectory.

### 3. 🧠 Behavioral Intelligence Engine
* **Weekend vs. Weekday Ratio:** Calculates the user's spending ratio between weekends (Sat/Sun) and weekdays (Mon–Fri) to detect leisure surges vs. commuter habits.
* **The "Chai Factor" / Micro-Expense Leak Detector:** Captures repetitive impulse purchases $\le$ ₹100, projects their 1-year annualized cost, and calculates the 10-year compounding lost wealth at a 12% index return.
* **Subscription Detector:** Automatically identifies repeated recurring monthly commitments (Netflix, Gym, Rent, Wi-Fi).

### 4. 🎯 Mathematical Decision Support
* **10-Year Opportunity Cost Calculator:** Simulates the true long-term price of discretionary purchases.
* **Emergency Fund Health Evaluator:** Scores liquid runway (in months) against average monthly essential living burn.
* **Goal Timeline Planner:** Calculates months required to fund milestone goals (e.g. Laptop, Bike) and simulates accelerated arrival through leak cuts.

### 5. 🤖 "Chanakya" GenAI Financial Coach
* Dynamic Context Injection: Compiles real-time metrics, behavioral leaks, and budget breaches into a clean markdown context string.
* Injects context into Google Gemini 2.5 Flash for personalized financial coaching.
* Includes a robust offline heuristic fallback engine when running without an API key.

---

## 🚀 Installation & Running Locally

```bash
# 1. Clone repository
git clone https://github.com/your-username/ai-finance-tracker.git
cd ai-finance-tracker

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # On Windows
source venv/bin/activate  # On macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up Google Gemini API key
# Create a .env file and add:
# GEMINI_API_KEY=your_gemini_api_key_here

# 5. Launch the Streamlit application
streamlit run app.py
```

---

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Database:** SQLite3
* **Data Processing & Analytics:** Pandas, NumPy
* **Visualization:** Plotly Express
* **Machine Learning:** Scikit-Learn (`TfidfVectorizer`, `MultinomialNB`, `joblib`)
* **Generative AI:** Google GenAI SDK (`gemini-2.5-flash`)
* **Frontend UI:** Streamlit
