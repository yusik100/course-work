from datetime import datetime, timedelta
from src.models import Loan

def test_pure_logic_due_date():
    borrowed_at = datetime.now()
    expected_due_date = (borrowed_at + timedelta(days=14)).date()
    loan = Loan(borrowed_at=borrowed_at, due_date=expected_due_date)
    assert loan.due_date == expected_due_date