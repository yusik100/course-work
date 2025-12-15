import pytest
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
from src.database import DATABASE_URL
from src.models import BookCopy, Reader, CopyStatus, Loan, Book, Genre, Author
from src.services import create_loan, return_book, delete_reader, report_lost_book
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
    if transaction.is_active:
        transaction.rollback() 
    connection.close()

def create_test_data(session):
    genre = Genre(name="Integration Genre")
    author = Author(full_name="Integration Author")
    book = Book(title="Integration Book", publication_year=2024, genre=genre, isbn="INT-123")
    book.authors.append(author)
    copy = BookCopy(inventory_number="INT-INV-001", status=CopyStatus.available, book=book)
    reader = Reader(first_name="Test", last_name="Integration", email="int@test.com")
    session.add_all([genre, author, book, copy, reader])
    session.commit()
    session.refresh(copy)
    session.refresh(reader)
    return copy, reader


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


def test_soft_delete_lost_book(db_session):

    copy, reader = create_test_data(db_session)
    
    report_lost_book(db_session, copy.id)

    db_session.refresh(copy)
    
    assert copy.status == CopyStatus.lost
    
    assert db_session.get(BookCopy, copy.id) is not None

def test_hard_delete_reader(db_session):

    copy, reader = create_test_data(db_session)
    reader_id = reader.id
    
    delete_reader(db_session, reader_id)
    
    deleted_reader = db_session.query(Reader).filter_by(id=reader_id).first()
    
    assert deleted_reader is None

def test_window_function_ranking(db_session):

    genre = Genre(name="Rank Genre")
    book = Book(title="Rank Book", publication_year=2024, genre=genre, isbn="RK-1")
    copy1 = BookCopy(inventory_number="RK-1", status=CopyStatus.available, book=book)
    copy2 = BookCopy(inventory_number="RK-2", status=CopyStatus.available, book=book)
    copy3 = BookCopy(inventory_number="RK-3", status=CopyStatus.available, book=book)
    
    reader_top = Reader(first_name="Top", last_name="Reader", email="top@test.com")
    reader_low = Reader(first_name="Low", last_name="Reader", email="low@test.com")
    
    db_session.add_all([genre, book, copy1, copy2, copy3, reader_top, reader_low])
    db_session.commit()
    
    create_loan(db_session, copy1.id, reader_top.id)
    create_loan(db_session, copy2.id, reader_top.id)
    
    create_loan(db_session, copy3.id, reader_low.id)
    
    subquery = db_session.query(
        Reader.id,
        func.count(Loan.id).label('total')
    ).join(Loan).group_by(Reader.id).subquery()
    
    results = db_session.query(
        subquery.c.id,
        subquery.c.total,
        func.rank().over(order_by=desc(subquery.c.total)).label('rank')
    ).all()
    
    assert len(results) >= 2
    
    top_stat = next(r for r in results if r.id == reader_top.id)
    low_stat = next(r for r in results if r.id == reader_low.id)
    
    assert top_stat.rank < low_stat.rank 
    
    assert top_stat.total == 2
    assert low_stat.total == 1