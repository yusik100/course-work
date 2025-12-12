import random
from datetime import datetime, timedelta

from src.database import SessionLocal
from src.models import Loan, Genre, Author, Book, BookCopy, Reader, CopyStatus

def seed_data():
    session = SessionLocal()

    try:
        print("Очищення старих даних...")
        session.query(Loan).delete()
        session.query(BookCopy).delete()
        session.query(Book).delete()
        session.query(Author).delete()
        session.query(Genre).delete()
        session.query(Reader).delete()
        session.commit()

        print("Починаємо наповнення бази...")

        # --- ЖАНРИ ---
        genres = [Genre(name="Фантастика"), Genre(name="Детектив"), Genre(name="Класика"), Genre(name="Наукова література")]
        session.add_all(genres)
        session.commit()

        # --- АВТОРИ ---
        orwell = Author(full_name="Джордж Орвелл", bio="Антиутопіст")
        rowling = Author(full_name="Дж.К. Роулінг", bio="Гаррі Поттер")
        pratchett = Author(full_name="Террі Пратчетт", bio="Фентезі-сатира")
        gaiman = Author(full_name="Ніл Ґейман", bio="Фентезі")
        king = Author(full_name="Стівен Кінг", bio="Король жахів")
        
        session.add_all([orwell, rowling, pratchett, gaiman, king])
        session.commit()

        # --- КНИГИ ---
        def get_isbn():
            return f"978-{random.randint(100,999)}-{random.randint(1000,9999)}-{random.randint(0,9)}"

        book1 = Book(title="1984", publication_year=1949, genre=genres[0], isbn=get_isbn())
        book1.authors.append(orwell)

        book2 = Book(title="Гаррі Поттер і філософський камінь", publication_year=1997, genre=genres[0], isbn=get_isbn())
        book2.authors.append(rowling)

        book3 = Book(title="Добрі знамення (Good Omens)", publication_year=1990, genre=genres[0], isbn=get_isbn())
        book3.authors = [pratchett, gaiman]

        book4 = Book(title="Сяйво", publication_year=1977, genre=genres[1], isbn=get_isbn())
        book4.authors.append(king)

        session.add_all([book1, book2, book3, book4])
        session.commit()

        # --- КОПІЇ ---
        all_books = session.query(Book).all()
        created_copies = []
        
        for book in all_books:
            for i in range(3):
                copy = BookCopy(
                    inventory_number=f"INV-{book.id}-{i+100}",
                    status=CopyStatus.available,
                    book=book
                )
                created_copies.append(copy)
                session.add(copy)
        session.commit()

        # --- ЧИТАЧІ ---
        readers = [
            Reader(first_name="Іван", last_name="Тестовий", email="ivan@test.com", phone_number="+380501112233"),
            Reader(first_name="Марія", last_name="Книголюб", email="maria@test.com", phone_number="+380971112233"),
            Reader(first_name="Петро", last_name="Студент", email="petro@test.com")
        ]
        session.add_all(readers)
        session.commit()

        # --- ІСТОРІЯ ВИДАЧ ---
        loan_closed = Loan(
            book_copy_id=created_copies[0].id,
            reader_id=readers[0].id,
            borrowed_at=datetime.now() - timedelta(days=10),
            due_date=datetime.now().date() + timedelta(days=20),
            returned_at=datetime.now()
        )
        
        active_copy = created_copies[1]
        active_copy.status = CopyStatus.on_loan
        
        loan_active = Loan(
            book_copy_id=active_copy.id,
            reader_id=readers[1].id,
            borrowed_at=datetime.now() - timedelta(days=2),
            due_date=datetime.now().date() + timedelta(days=12),
            returned_at=None
        )

        session.add(loan_closed)
        session.add(loan_active)
        session.add(active_copy)

        session.commit()
        print("База успішно наповнена даними!")

    except Exception as e:
        print(f"Сталася помилка: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()