import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from src.database import DATABASE_URL
from src.models import BookCopy, Reader, CopyStatus, Loan, Book, Genre, Author
from src.services import create_loan, return_book, report_lost_book
import os


@pytest.fixture(scope="module")
def engine():
    return create_engine(os.getenv("DATABASE_URL", DATABASE_URL))

@pytest.fixture(scope="function")
def db_session(engine):

    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def create_test_data(session):
    genre = Genre(name="Unit Test Genre")
    author = Author(full_name="Unit Test Author")
    book = Book(title="Unit Test Book", publication_year=2024, genre=genre, isbn="UT-123")
    book.authors.append(author)
    copy = BookCopy(inventory_number="UT-INV-001", status=CopyStatus.available, book=book)
    reader = Reader(first_name="Test", last_name="Unit", email="unit@test.com")
    session.add_all([genre, author, book, copy, reader])
    session.commit()
    return copy, reader

def test_pure_logic_due_date():

    borrowed_at = datetime.now()
    expected_due_date = (borrowed_at + timedelta(days=14)).date()
    
    loan = Loan(borrowed_at=borrowed_at, due_date=expected_due_date)
    
    assert loan.due_date == expected_due_date
    assert loan.returned_at is None


def test_crud_lifecycle(db_session):

    copy, reader = create_test_data(db_session)

    loan = create_loan(db_session, copy.id, reader.id)
    assert loan.id is not None
    
    db_session.refresh(copy)
    assert copy.status == CopyStatus.on_loan

    return_book(db_session, copy.id)
    db_session.refresh(copy)
    assert copy.status == CopyStatus.available
    assert loan.returned_at is not None


def test_error_handling_unavailable_book(db_session):

    copy, reader = create_test_data(db_session)

    create_loan(db_session, copy.id, reader.id)

    with pytest.raises(ValueError) as error_info:
        create_loan(db_session, copy.id, reader.id)

    assert "недоступна" in str(error_info.value)


def test_analytics_data_integrity(db_session):

    genre = Genre(name="Analytics Genre")
    book = Book(title="B1", publication_year=2020, genre=genre, isbn="A1")
    copy1 = BookCopy(inventory_number="A-1", status=CopyStatus.available, book=book)
    copy2 = BookCopy(inventory_number="A-2", status=CopyStatus.available, book=book)
    reader = Reader(first_name="An", last_name="Alytics", email="a@a.com")
    
    db_session.add_all([genre, book, copy1, copy2, reader])
    db_session.commit()
    
    create_loan(db_session, copy1.id, reader.id)
    create_loan(db_session, copy2.id, reader.id)
    
    result = db_session.query(
        Genre.name,
        func.count(Loan.id)
    )\
    .join(Book).join(BookCopy).join(Loan)\
    .filter(Genre.name == "Analytics Genre")\
    .group_by(Genre.name)\
    .first()
    
    assert result is not None
    name, count = result
    assert name == "Analytics Genre"
    assert count == 2