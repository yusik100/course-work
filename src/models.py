import enum
from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, DateTime, Text,
    Enum as SQLEnum, CheckConstraint, Index, func, Table
)
from sqlalchemy.orm import relationship
from .database import Base


class CopyStatus(enum.Enum):
    available = "available"
    on_loan = "on_loan"
    lost = "lost"
    maintenance = "maintenance"


book_authors = Table(
    'book_authors',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True)
)

class Genre(Base):
    __tablename__ = 'genres'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    books = relationship("Book", back_populates="genre")

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    bio = Column(Text)
    
    books = relationship("Book", secondary=book_authors, back_populates="authors", passive_deletes=True)

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    isbn = Column(String, unique=True)
    publication_year = Column(Integer)
    
    genre_id = Column(Integer, ForeignKey('genres.id', ondelete='SET NULL'), nullable=True)
    
    authors = relationship("Author", secondary=book_authors, back_populates="books", passive_deletes=True)
    genre = relationship("Genre", back_populates="books")
    
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        CheckConstraint("publication_year IS NULL OR publication_year > 0", name="ck_book_pub_year_positive"),
        Index('ix_books_title', 'title'),
    )

class BookCopy(Base):
    __tablename__ = 'book_copies'
    id = Column(Integer, primary_key=True)
    inventory_number = Column(String, unique=True, nullable=False)
    status = Column(SQLEnum(CopyStatus, name='copy_status'), nullable=False, server_default=CopyStatus.available.value)
    
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    
    book = relationship("Book", back_populates="copies")
    loans = relationship("Loan", back_populates="copy", cascade="all, delete-orphan")

class Reader(Base):
    __tablename__ = 'readers'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=True)
    
    loans = relationship("Loan", back_populates="reader", cascade="all, delete-orphan")
    
    __table_args__ = (Index('ix_readers_email', 'email'),)

class Loan(Base):
    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    borrowed_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(Date, nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    
    book_copy_id = Column(Integer, ForeignKey('book_copies.id', ondelete='CASCADE'), nullable=False)
    reader_id = Column(Integer, ForeignKey('readers.id', ondelete='CASCADE'), nullable=False)
    
    copy = relationship("BookCopy", back_populates="loans")
    reader = relationship("Reader", back_populates="loans")

    __table_args__ = (
        CheckConstraint("(returned_at IS NULL) OR (returned_at >= borrowed_at)", name="ck_loan_returned_after_borrowed"),
        
        Index(
            'ux_loans_active_per_copy', 
            'book_copy_id', 
            unique=True, 
            postgresql_where=(returned_at == None)
        ),
    )