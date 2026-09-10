from config import  CURRENCY_SYMBOLS,EXPENSE_CATEGORIES

def format_amount(amount):
    return f"{CURRENCY_SYMBOLS}{amount:,.2f}"

def create_transaction(date,amount,category,txtype,note=" "):
    transaction={
        "date":date,
        "amount":amount,
        "category":category,
        "type":txtype,
        "note":note,
    }
    return transaction

if __name__ == "__main__":
    print(format_amount(350))
    print(format_amount(40000))
    print(format_amount(5000))
    
    tx=create_transaction("2026-09-02",350,'Food & Dining','Expense',note="Swiggy dinner")
    print(tx)

    print(f"You spent {format_amount(tx['amount'])} on  {tx['category']}")
    
    print("\n Available Categories")
    for i,cat in enumerate(EXPENSE_CATEGORIES,start=1):
        print(f"{i}.{cat}")