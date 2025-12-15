from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.models import Book, Loan, Reader, Genre, BookCopy, Author
from datetime import datetime


def get_books_by_genre(session: Session, genre_name: str):

    print(f"\nПошук книг жанру: '{genre_name}'")
    
    books = session.query(Book)\
        .join(Genre)\
        .filter(Genre.name == genre_name)\
        .order_by(desc(Book.publication_year))\
        .all()

    if not books:
        print("Нічого не знайдено.")
    else:
        for book in books:
            authors = ", ".join([a.full_name for a in book.authors])
            print(f"{book.title} ({book.publication_year}) — {authors}")


def get_overdue_loans(session: Session):

    print(f"\nЗвіт: Боржники")
    
    overdue_loans = session.query(Loan).filter(
        Loan.returned_at == None,
        Loan.due_date < datetime.now().date()
    ).all()

    if not overdue_loans:
        print("Боржників немає! Всі повернули книги вчасно.")
    else:
        for loan in overdue_loans:
            delay = (datetime.now().date() - loan.due_date).days
            print(f"{loan.reader.first_name} {loan.reader.last_name}: "
                  f"книга '{loan.copy.book.title}' прострочена на {delay} днів/")


def get_top_readers(session: Session):

    print(f"\nТоп-5 читачів")
    
    results = session.query(
        Reader.first_name,
        Reader.last_name,
        func.count(Loan.id).label('total_books')
    )\
    .join(Loan)\
    .group_by(Reader.id)\
    .order_by(desc('total_books'))\
    .limit(5)\
    .all()

    if not results:
        print("Даних ще немає.")
    
    for i, (first, last, count) in enumerate(results, 1):
        print(f"{i}. {first} {last} — взяв(ла) {count} книг")

def get_genre_popularity(session: Session):

    print(f"\nПопулярність жанрів")

    results = session.query(
        Genre.name,
        func.count(Loan.id).label('loan_count')
    )\
    .select_from(Genre)\
    .join(Book)\
    .join(BookCopy)\
    .join(Loan)\
    .group_by(Genre.name)\
    .order_by(desc('loan_count'))\
    .all()
    
    for genre, count in results:
        print(f"{genre}: видано {count} разів")