"""
Central configuration for the AI Finance Tracker & Decision-Support System.
"""

CURRENCY_SYMBOLS = "₹"
CURRENCY_CODE = "INR"

EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Rent & Housing",
    "Utilities",
    "Transport",
    "Shopping",
    "Entertainment",
    "Health & Fitness",
    "Education",
    "Other",
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investments",
    "Other Income",
]

TRANSACTION_TYPES = ["Expense", "Income"]

DEFAULT_BUDGETS = {
    "Food & Dining": 5000,
    "Groceries": 4000,
    "Transport": 2000,
    "Shopping": 3000,
    "Entertainment": 1500,
    "Utilities": 2500,
    "Rent & Housing": 15000,
    "Health & Fitness": 2000,
    "Education": 5000,
}
