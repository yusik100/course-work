import random
from datetime import datetime, timedelta
from src.database import SessionLocal
from src.models import Loan, Genre, Author, Book, BookCopy, Reader, CopyStatus

FIRST_NAMES = ["Олександр", "Дмитро", "Максим", "Артем", "Іван", "Микола", "Сергій", "Андрій", "Ольга", "Анна", "Юлія", "Марія", "Тетяна", "Олена", "Наталія", "Ірина"]
LAST_NAMES = ["Коваленко", "Бондаренко", "Ткаченко", "Шевченко", "Кравченко", "Бойко", "Мельник", "Лисенко", "Поліщук", "Гаврилюк"]
BOOK_DATA = [
    ("Фантастика", "Дюна", "Френк Герберт", 1965),
    ("Фантастика", "Фундація", "Айзек Азімов", 1951),
    ("Фантастика", "Гіперіон", "Ден Сіммонс", 1989),
    ("Фантастика", "Соляріс", "Станіслав Лем", 1961),
    ("Детектив", "Вбивство у Східному експресі", "Агата Крісті", 1934),
    ("Детектив", "Шерлок Холмс", "Артур Конан Дойл", 1887),
    ("Детектив", "Код да Вінчі", "Ден Браун", 2003),
    ("Класика", "Гордість і упередження", "Джейн Остін", 1813),
    ("Класика", "Великий Гетсбі", "Ф. Скотт Фіцджеральд", 1925),
    ("Класика", "1984", "Джордж Орвелл", 1949),
    ("Класика", "Майстер і Маргарита", "Михайло Булгаков", 1967),
    ("Наукова література", "Коротка історія часу", "Стівен Гокінг", 1988),
    ("Наукова література", "Sapiens", "Ювал Ной Харарі", 2011),
    ("Наукова література", "Егоїстичний ген", "Річард Докінз", 1976),
    ("Фентезі", "Гаррі Поттер", "Дж.К. Роулінг", 1997),
    ("Фентезі", "Володар Перснів", "Дж.Р.Р. Толкін", 1954),
    ("Фентезі", "Хоббіт", "Дж.Р.Р. Толкін", 1937),
    ("Жахи", "Воно", "Стівен Кінг", 1986),
    ("Жахи", "Сяйво", "Стівен Кінг", 1977),
]

def get_isbn():
    return f"978-{random.randint(100,999)}-{random.randint(1000,9999)}-{random.randint(0,9)}"

def seed_data():
    session = SessionLocal()
    try:
        print("Очищення бази даних...")
        session.query(Loan).delete()
        session.query(BookCopy).delete()
        session.query(Book).delete()
        session.query(Author).delete()
        session.query(Genre).delete()
        session.query(Reader).delete()
        session.commit()

        print("Створення книг та авторів...")
        
        genres_cache = {}
        authors_cache = {}
        books_list = []

        for genre_name, title, author_name, year in BOOK_DATA:
            if genre_name not in genres_cache:
                g = Genre(name=genre_name)
                session.add(g)
                genres_cache[genre_name] = g
            
            if author_name not in authors_cache:
                a = Author(full_name=author_name)
                session.add(a)
                authors_cache[author_name] = a
            
            book = Book(
                title=title,
                publication_year=year,
                genre=genres_cache[genre_name],
                isbn=get_isbn()
            )
            book.authors.append(authors_cache[author_name])
            session.add(book)
            books_list.append(book)
        
        session.commit()

        print("Створення копій...")
        all_copies = []
        for book in books_list:
            count = random.randint(2, 5)
            for i in range(count):
                copy = BookCopy(
                    inventory_number=f"INV-{book.id}-{i+1000}",
                    status=CopyStatus.available,
                    book=book
                )
                session.add(copy)
                all_copies.append(copy)
        session.commit()

        print("Генерація читачів...")
        readers_list = []
        for _ in range(30):
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            email = f"{fname.lower()}.{lname.lower()}{random.randint(1,999)}@example.com"
            
            reader = Reader(first_name=fname, last_name=lname, email=email)
            session.add(reader)
            readers_list.append(reader)
        session.commit()

        print("Генерація історії видач...")
        
        for reader in readers_list:
            loans_count = random.randint(0, 8)
            
            for _ in range(loans_count):
                copy = random.choice(all_copies)

                days_ago = random.randint(30, 180)
                borrowed = datetime.now() - timedelta(days=days_ago)
                returned = borrowed + timedelta(days=random.randint(5, 15))
                
                loan = Loan(
                    book_copy_id=copy.id,
                    reader_id=reader.id,
                    borrowed_at=borrowed,
                    due_date=borrowed + timedelta(days=14),
                    returned_at=returned
                )
                session.add(loan)

        debtor_copies = random.sample(all_copies, 7)
        
        for copy in debtor_copies:
            reader = random.choice(readers_list)

            days_ago = random.randint(20, 40)
            borrowed = datetime.now() - timedelta(days=days_ago)
            
            loan = Loan(
                book_copy_id=copy.id,
                reader_id=reader.id,
                borrowed_at=borrowed,
                due_date=borrowed + timedelta(days=14),
                returned_at=None 
            )
            copy.status = CopyStatus.on_loan
            session.add(copy)
            session.add(loan)

        session.commit()
        print(f"База успішно наповнена.")

    except Exception as e:
        print(f"Помилка: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()