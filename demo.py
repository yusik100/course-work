from src.database import SessionLocal
from src.services import create_loan, return_book
from src.queries import get_books_by_genre, get_overdue_loans, get_top_readers, get_genre_popularity, get_reader_ranks
from src.models import BookCopy, Reader, CopyStatus

def run_demonstration():
    session = SessionLocal()
    print("\n" + "="*50)
    print("БІБЛІОТЕЧНА СИСТЕМА: ДЕМОНСТРАЦІЯ")
    print("="*50)
    
    try:
        print("\nЧАСТИНА 1: АНАЛІТИКА ТА ЗВІТИ")
        print("-" * 30)

        get_top_readers(session)

        print(f"\nРейтинг читачів (RANK):")
        ranks = get_reader_ranks(session)
        for first, last, count, rank in ranks[:10]: 
            print(f"Ранг {rank}: {first} {last} — прочитав {count} книг")
        if len(ranks) > 10:
            print("... (і ще інші читачі)")

        get_genre_popularity(session)

        get_overdue_loans(session)      

        get_books_by_genre(session, "Фантастика")

        print("\n\nЧАСТИНА 2: ЖИВИЙ ПРОЦЕС (Видача/Повернення)")
        print("-" * 30)

        available_copy = session.query(BookCopy).filter(BookCopy.status == CopyStatus.available).first()
        reader = session.query(Reader).first()

        if not available_copy or not reader:
            print("Увага: Недостатньо даних для демо. Запустіть seed.py!")
            return

        print(f"Читач: {reader.first_name} {reader.last_name}")
        print(f"Книга: '{available_copy.book.title}' (Інв. № {available_copy.inventory_number})")

        print("\nВидаємо книгу...")
        create_loan(session, book_copy_id=available_copy.id, reader_id=reader.id)
        print("Успішно видано.")

        print("\nСпроба видати ту ж саму книгу ще раз...")
        try:
            create_loan(session, book_copy_id=available_copy.id, reader_id=reader.id)
        except ValueError as e:
            print(f"СИСТЕМА ЗАХИСТУ СПРАЦЮВАЛА: {e}")

        print("\nЧитач повертає книгу...")
        return_book(session, book_copy_id=available_copy.id)
        print("Книгу успішно повернуто.")

    except Exception as e:
        print(f"\nКРИТИЧНА ПОМИЛКА: {e}")
    finally:
        session.close()
        print("\n" + "="*50)
        print("ДЕМОНСТРАЦІЮ ЗАВЕРШЕНО")
        print("="*50)

if __name__ == "__main__":
    run_demonstration()