from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.models import Loan, BookCopy, Reader, CopyStatus

def create_loan(session: Session, book_copy_id: int, reader_id: int, days: int = 14):
    print(f"\nСпроба видати копію #{book_copy_id} читачеві #{reader_id}")

    try:
        copy = session.query(BookCopy).filter(BookCopy.id == book_copy_id).first()
        if not copy:
            raise ValueError(f"Помилка: Копію книги з ID {book_copy_id} не знайдено.")

        reader = session.query(Reader).filter(Reader.id == reader_id).first()
        if not reader:
            raise ValueError(f"Помилка: Читача з ID {reader_id} не знайдено.")

        if copy.status != CopyStatus.available:
            raise ValueError(f"Відмова: Ця книга зараз недоступна (Статус: {copy.status.value})")

        new_loan = Loan(
            book_copy_id=copy.id,
            reader_id=reader.id,
            borrowed_at=datetime.now(),
            due_date=datetime.now().date() + timedelta(days=days),
            returned_at=None
        )
        session.add(new_loan)

        copy.status = CopyStatus.on_loan
        session.add(copy)

        session.commit()
        session.refresh(new_loan)

        print(f"Книгу '{copy.book.title}' видано.")
        print(f"Запис #{new_loan.id}, повернути до {new_loan.due_date}")

        return new_loan

    except Exception as e:
        session.rollback()
        raise e


def return_book(session: Session, book_copy_id: int):
    print(f"\nСпроба повернути копію #{book_copy_id}")

    try:
        loan = session.query(Loan).filter(
            Loan.book_copy_id == book_copy_id,
            Loan.returned_at == None
        ).first()

        if not loan:
            raise ValueError(f"Помилка: Ця книга (ID {book_copy_id}) зараз не числиться як видана.")

        loan.returned_at = datetime.now()
        session.add(loan)

        loan.copy.status = CopyStatus.available
        session.add(loan.copy)

        session.commit()
        
        print(f"Книгу повернуто. Дата закриття: {loan.returned_at}")
        return loan

    except Exception as e:
        session.rollback()
        raise e
    

def delete_reader(session: Session, reader_id: int):
    print(f"\nСпроба видалити читача #{reader_id}")
    
    try:
        reader = session.query(Reader).filter(Reader.id == reader_id).first()
        if not reader:
            raise ValueError(f"Читача {reader_id} не знайдено")

        name = f"{reader.first_name} {reader.last_name}"
        loans_count = len(reader.loans) 

        session.delete(reader)
        session.commit()

        print(f"Читача '{name}' успішно видалено.")
        print(f"Також автоматично видалено {loans_count} записів з його історії (CASCADE).")
        
        return {
            "status": "deleted", 
            "reader_id": reader_id, 
            "name": name, 
            "loans_deleted": loans_count
        }
    
    except Exception as e:
        session.rollback()
        raise e


def report_lost_book(session: Session, book_copy_id: int):
    print(f"\nСписання книги #{book_copy_id} (Втрачена)")
    
    try:
        copy = session.query(BookCopy).filter(BookCopy.id == book_copy_id).first()
        if not copy:
            raise ValueError(f"Копію {book_copy_id} не знайдено")

        copy.status = CopyStatus.lost
        session.add(copy)
        session.commit()

        print(f"Книгу '{copy.book.title}' позначено як ВТРАЧЕНУ.")
        print("Вона більше не доступна для видачі, але залишилась в базі.")
        
        return copy

    except Exception as e:
        session.rollback()
        raise e