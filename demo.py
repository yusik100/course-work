from datetime import datetime, timedelta
from src.database import SessionLocal
from src.services import create_loan, return_book, delete_reader, report_lost_book
from src.queries import get_books_by_genre, get_overdue_loans, get_top_readers, get_genre_popularity
from src.models import BookCopy, Reader, CopyStatus, Loan


def run_full_demonstration():
    session = SessionLocal()
    print("Демонстрація системи")
    
    try:
        available_copy = session.query(BookCopy).filter(BookCopy.status == CopyStatus.available).first()
        reader = session.query(Reader).first()

        if not available_copy or not reader:
            print("Помилка: Запустіть 'python seed.py' перед демо.")
            return

        print(f"Робоча книга: '{available_copy.book.title}' (ID: {available_copy.id})")
        print(f"Робочий читач: {reader.first_name} {reader.last_name}")

        print("\nСЦЕНАРІЙ 1: Видача книги")
        create_loan(session, book_copy_id=available_copy.id, reader_id=reader.id)

        print("\nСЦЕНАРІЙ 2: Перевірка захисту (спроба взяти зайняту)")
        try:
            create_loan(session, book_copy_id=available_copy.id, reader_id=reader.id)
        except ValueError as e:
            print(f"Система захисту спрацювала: {e}")

        print("\nСЦЕНАРІЙ 3: Повернення книги")
        return_book(session, book_copy_id=available_copy.id)

        print("\n" + "="*40)
        print(" БЛОК АНАЛІТИКИ")
        print("="*40)

        bad_loan = Loan(
            book_copy_id=available_copy.id,
            reader_id=reader.id,
            borrowed_at=datetime.now() - timedelta(days=100),
            due_date=datetime.now().date() - timedelta(days=80),
            returned_at=None
        )

        available_copy.status = CopyStatus.on_loan
        session.add(bad_loan)
        session.add(available_copy)
        session.commit()
        print("\n(Створено штучного боржника для тесту звіту)")

        get_books_by_genre(session, "Фантастика")
        get_overdue_loans(session)
        get_top_readers(session)
        get_genre_popularity(session)

        session.delete(bad_loan)
        available_copy.status = CopyStatus.available
        session.commit()

        print("\n" + "="*40)
        print(" БЛОК ВИДАЛЕННЯ")
        print("="*40)

        temp_reader = Reader(first_name="Temp", last_name="DeleteMe", email="temp@del.com")
        session.add(temp_reader)
        session.commit()
        create_loan(session, book_copy_id=available_copy.id, reader_id=temp_reader.id)
        
        print("\nСЦЕНАРІЙ 4: Жорстке видалення читача (Hard Delete)")
        delete_reader(session, reader_id=temp_reader.id)

        available_copy.status = CopyStatus.available
        session.add(available_copy)
        session.commit()

        print("\nСЦЕНАРІЙ 5: Списання книги (Soft Delete)")
        report_lost_book(session, book_copy_id=available_copy.id)

    except Exception as e:
        print(f"Виникла помилка: {e}")
    finally:
        session.close()
        print("\nДемонстрацію завершено.")

if __name__ == "__main__":
    run_full_demonstration()