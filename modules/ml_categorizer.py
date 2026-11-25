"""
modules/ml_categorizer.py
Machine Learning Automated Transaction Categorizer.
Uses TF-IDF (Term Frequency-Inverse Document Frequency) + Naive Bayes / Logistic Regression
to predict transaction category based on note text (e.g. 'swiggy' -> 'Food & Dining').
"""

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MODEL_PATH = "modules/categorizer_model.joblib"

DEFAULT_TRAINING_DATA = [
    # Food & Dining
    ("swiggy dinner", "Food & Dining"),
    ("zomato pizza order", "Food & Dining"),
    ("mcdonalds burger meal", "Food & Dining"),
    ("starbucks cold coffee", "Food & Dining"),
    ("chai tapri snack samosa", "Food & Dining"),
    ("lunch with friends cafe", "Food & Dining"),
    ("biryani party dinner", "Food & Dining"),
    ("subway sandwich lunch", "Food & Dining"),
    ("dominos garlic bread", "Food & Dining"),
    ("bikanervala sweets rasgulla", "Food & Dining"),

    # Groceries
    ("blinkit milk bread eggs", "Groceries"),
    ("zepto vegetables tomato onion", "Groceries"),
    ("instamart cooking oil atta rice", "Groceries"),
    ("supermarket monthly ration grocery", "Groceries"),
    ("dmart grocery shopping", "Groceries"),
    ("vegetable fruit market mandi", "Groceries"),
    ("amul butter paneer curd", "Groceries"),

    # Transport
    ("uber cab office ride", "Transport"),
    ("ola auto fare", "Transport"),
    ("rapido bike taxi", "Transport"),
    ("metro card recharge smartcard", "Transport"),
    ("petrol fuel indian oil hp pump", "Transport"),
    ("diesel car fill up", "Transport"),
    ("parking fee mall station", "Transport"),
    ("toll plaza fastag recharge", "Transport"),

    # Utilities
    ("electricity bill bescom bses", "Utilities"),
    ("broadband wifi internet airtel fiber", "Utilities"),
    ("jio mobile recharge monthly plan", "Utilities"),
    ("water bill municipal corporation", "Utilities"),
    ("piped gas lpg cylinder refill", "Utilities"),
    ("society maintenance charges flat", "Utilities"),

    # Shopping
    ("amazon clothes shoes headphones", "Shopping"),
    ("flipkart sale purchase laptop bag", "Shopping"),
    ("myntra t-shirt jeans jacket", "Shopping"),
    ("zara casual shirt sneakers", "Shopping"),
    ("h&m hoodie dress shopping", "Shopping"),
    ("electronics charger mouse usb cable", "Shopping"),

    # Entertainment
    ("netflix monthly 4k subscription", "Entertainment"),
    ("spotify premium music subscription", "Entertainment"),
    ("bookmyshow movie tickets pvr", "Entertainment"),
    ("hotstar cricket match streaming", "Entertainment"),
    ("prime video amazon prime recharge", "Entertainment"),
    ("gaming steam game purchase", "Entertainment"),

    # Rent & Housing
    ("house rent monthly flat transfer", "Rent & Housing"),
    ("pg accommodation room rent", "Rent & Housing"),
    ("flat rent owner bank transfer", "Rent & Housing"),
    ("brokerage house security deposit", "Rent & Housing"),

    # Health & Fitness
    ("cult fit gym membership annual", "Health & Fitness"),
    ("gym fee trainer protein powder", "Health & Fitness"),
    ("apollo pharmacy medicine strip", "Health & Fitness"),
    ("1mg lab test blood checkup", "Health & Fitness"),
    ("dentist doctor consultation fee", "Health & Fitness"),

    # Education
    ("coursera course certificate", "Education"),
    ("udemy python web development course", "Education"),
    ("college exam semester fees", "Education"),
    ("books study material novel stationary", "Education"),
    ("library membership fee", "Education"),

    # Other
    ("donation temple charity ngo", "Other"),
    ("gift for friend birthday", "Other"),
    ("laundry dry clean clothes", "Other"),
    ("barber haircut salon grooming", "Other"),
]


class TransactionCategorizer:
    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, stop_words="english")),
            ("clf", MultinomialNB(alpha=0.1)),
        ])
        self.is_trained = False
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.pipeline = joblib.load(MODEL_PATH)
                self.is_trained = True
                return
            except Exception:
                pass
        self.train_default()

    def train_default(self):
        df_train = pd.DataFrame(DEFAULT_TRAINING_DATA, columns=["note", "category"])
        self.fit(df_train["note"], df_train["category"])

    def fit(self, texts, labels):
        cleaned_texts = [str(t).strip().lower() for t in texts]
        self.pipeline.fit(cleaned_texts, labels)
        self.is_trained = True
        try:
            joblib.dump(self.pipeline, MODEL_PATH)
        except Exception:
            pass

    def train_on_history(self, df):
        """Fine-tunes model on user's own transaction history if available."""
        if df is None or df.empty:
            return
        valid = df.dropna(subset=["note", "category"])
        valid = valid[valid["note"].str.strip() != ""]
        if len(valid) >= 10:
            combined_texts = list(valid["note"]) + [t[0] for t in DEFAULT_TRAINING_DATA]
            combined_labels = list(valid["category"]) + [t[1] for t in DEFAULT_TRAINING_DATA]
            self.fit(combined_texts, combined_labels)

    def predict(self, note):
        """Predicts most probable category from transaction note text."""
        if not note or not str(note).strip():
            return None
        cleaned = str(note).strip().lower()
        try:
            pred = self.pipeline.predict([cleaned])[0]
            # Check confidence
            probs = self.pipeline.predict_proba([cleaned])[0]
            confidence = max(probs)
            return pred if confidence >= 0.25 else None
        except Exception:
            return None


# Global singleton instance
_categorizer_instance = None


def get_categorizer():
    global _categorizer_instance
    if _categorizer_instance is None:
        _categorizer_instance = TransactionCategorizer()
    return _categorizer_instance


def suggest_category(note):
    """Public helper function for UI auto-suggestion."""
    cat = get_categorizer()
    return cat.predict(note)
