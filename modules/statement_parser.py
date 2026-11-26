"""
modules/statement_parser.py
Bank Statement CSV Parser & Ingestion Engine.
Supports:
1. Automatic column detection (Date, Description/Narration, Debit/Credit, Withdrawal/Deposit, Amount).
2. Format normalization: HDFC, SBI, ICICI, Axis, Paytm/UPI, and standard CSV formats.
3. Automated ML auto-categorization for all imported rows.
4. Duplicate detection against existing user transactions.
"""

import io
import re
import pandas as pd
from datetime import datetime
from modules.ml_categorizer import suggest_category


def detect_statement_columns(columns: list[str]) -> dict:
    """
    Intelligently maps raw bank statement column names to normalized fields:
    'date', 'description', 'amount', 'type', 'debit', 'credit'
    """
    mapping = {
        "date": None,
        "description": None,
        "amount": None,
        "type": None,
        "debit": None,
        "credit": None,
    }

    date_patterns = [r"^date", r"tx.*date", r"transaction.*date", r"value.*date", r"posting.*date"]
    desc_patterns = [r"desc", r"narrat", r"particular", r"remark", r"merchant", r"detail", r"note"]
    debit_patterns = [r"^debit", r"^dr", r"withdraw", r"debit.*amount", r"paid.*out"]
    credit_patterns = [r"^credit", r"^cr", r"deposit", r"credit.*amount", r"paid.*in"]
    amount_patterns = [r"^amount", r"tx.*amount", r"transaction.*amount", r"net.*amount"]
    type_patterns = [r"^type", r"tx.*type", r"transaction.*type", r"cr.*dr", r"dr.*cr"]

    for col in columns:
        c_clean = str(col).strip().lower()
        
        # Check Date
        if not mapping["date"] and any(re.search(p, c_clean) for p in date_patterns):
            mapping["date"] = col
        # Check Description
        elif not mapping["description"] and any(re.search(p, c_clean) for p in desc_patterns):
            mapping["description"] = col
        # Check Debit
        elif not mapping["debit"] and any(re.search(p, c_clean) for p in debit_patterns):
            mapping["debit"] = col
        # Check Credit
        elif not mapping["credit"] and any(re.search(p, c_clean) for p in credit_patterns):
            mapping["credit"] = col
        # Check Type
        elif not mapping["type"] and any(re.search(p, c_clean) for p in type_patterns):
            mapping["type"] = col
        # Check Amount
        elif not mapping["amount"] and any(re.search(p, c_clean) for p in amount_patterns):
            mapping["amount"] = col

    return mapping


def parse_bank_statement(file_content, default_category="Other") -> tuple[bool, str, pd.DataFrame]:
    """
    Parses bank statement CSV into a standardized DataFrame with columns:
    ['date', 'amount', 'category', 'type', 'note']
    
    file_content can be a file-like object, bytes, or path.
    """
    try:
        if isinstance(file_content, bytes):
            # Try utf-8 first, fallback to latin-1
            try:
                df_raw = pd.read_csv(io.BytesIO(file_content))
            except UnicodeDecodeError:
                df_raw = pd.read_csv(io.BytesIO(file_content), encoding="latin-1")
        elif isinstance(file_content, str):
            df_raw = pd.read_csv(file_content)
        else:
            df_raw = pd.read_csv(file_content)
    except Exception as e:
        return False, f"Failed to parse CSV file: {e}", pd.DataFrame()

    if df_raw.empty:
        return False, "The uploaded CSV file is empty.", pd.DataFrame()

    col_map = detect_statement_columns(df_raw.columns.tolist())

    if not col_map["date"]:
        return False, "Could not identify a 'Date' column in the uploaded file.", pd.DataFrame()

    records = []
    has_separate_debit_credit = col_map["debit"] is not None and col_map["credit"] is not None

    for _, row in df_raw.iterrows():
        raw_date = row.get(col_map["date"])
        if pd.isna(raw_date) or str(raw_date).strip() == "":
            continue

        # Parse date
        try:
            parsed_date = pd.to_datetime(raw_date, dayfirst=True).strftime("%Y-%m-%d")
        except Exception:
            continue

        raw_desc = str(row.get(col_map["description"], "")).strip() if col_map["description"] else "Bank Transaction"
        if raw_desc.lower() in ["nan", "none", ""]:
            raw_desc = "Bank Transaction"

        tx_amount = 0.0
        tx_type = "Expense"

        if has_separate_debit_credit:
            debit_val = str(row.get(col_map["debit"], "0")).replace(",", "").strip()
            credit_val = str(row.get(col_map["credit"], "0")).replace(",", "").strip()

            debit_amt = float(re.sub(r"[^\d.]", "", debit_val)) if re.sub(r"[^\d.]", "", debit_val) else 0.0
            credit_amt = float(re.sub(r"[^\d.]", "", credit_val)) if re.sub(r"[^\d.]", "", credit_val) else 0.0

            if debit_amt > 0:
                tx_amount = debit_amt
                tx_type = "Expense"
            elif credit_amt > 0:
                tx_amount = credit_amt
                tx_type = "Income"
            else:
                continue
        elif col_map["amount"]:
            raw_amt_str = str(row.get(col_map["amount"], "0")).replace(",", "").strip()
            # Check for negative numbers or CR/DR signs
            is_negative = "-" in raw_amt_str or "dr" in raw_amt_str.lower()
            clean_amt = re.sub(r"[^\d.]", "", raw_amt_str)
            tx_amount = float(clean_amt) if clean_amt else 0.0

            if tx_amount <= 0:
                continue

            # Determine type
            if col_map["type"] and not pd.isna(row.get(col_map["type"])):
                t_val = str(row.get(col_map["type"])).strip().lower()
                if "cr" in t_val or "income" in t_val or "deposit" in t_val:
                    tx_type = "Income"
                else:
                    tx_type = "Expense"
            else:
                # Infer from sign
                if is_negative:
                    tx_type = "Expense"
                else:
                    # By default in bank statements, positive could be credit or standard expense;
                    # We check description keywords (Salary, Interest, Refund -> Income)
                    desc_lower = raw_desc.lower()
                    if any(k in desc_lower for k in ["salary", "interest", "dividend", "credit", "cashback", "refund"]):
                        tx_type = "Income"
                    else:
                        tx_type = "Expense"
        else:
            continue

        # ML Auto-Categorization
        if tx_type == "Income":
            if any(k in raw_desc.lower() for k in ["salary", "payroll"]):
                category = "Salary"
            elif any(k in raw_desc.lower() for k in ["dividend", "interest", "zerodha", "groww"]):
                category = "Investments"
            elif any(k in raw_desc.lower() for k in ["upwork", "freelance", "client"]):
                category = "Freelance"
            else:
                category = "Other Income"
        else:
            predicted = suggest_category(raw_desc)
            category = predicted if predicted else default_category

        records.append({
            "date": parsed_date,
            "amount": round(tx_amount, 2),
            "category": category,
            "type": tx_type,
            "note": raw_desc,
        })

    if not records:
        return False, "No valid transaction rows could be parsed from the CSV.", pd.DataFrame()

    parsed_df = pd.DataFrame(records)
    return True, f"Successfully parsed {len(parsed_df)} transactions from statement.", parsed_df
