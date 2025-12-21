from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import SessionLocal, engine, Base
from src import models, queries, services

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Бібліотечна API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/books/genre/{genre_name}", tags=["Books"])
def get_books_by_genre_endpoint(genre_name: str, db: Session = Depends(get_db)):
    books = queries.get_books_by_genre(db, genre_name)
    if not books:
        raise HTTPException(status_code=404, detail="Книг цього жанру не знайдено")
    return books

@app.get("/analytics/overdue", tags=["Analytics"])
def get_overdue_endpoint(db: Session = Depends(get_db)):
    return queries.get_overdue_loans(db)

@app.get("/analytics/top-readers", tags=["Analytics"])
def get_top_readers_endpoint(db: Session = Depends(get_db)):
    return queries.get_top_readers(db)

@app.get("/analytics/genres", tags=["Analytics"])
def get_genre_stats_endpoint(db: Session = Depends(get_db)):
    return queries.get_genre_popularity(db)

@app.get("/analytics/ranks", tags=["Analytics"])
def get_reader_ranks_endpoint(db: Session = Depends(get_db)):
    return queries.get_reader_ranks(db)


@app.post("/loans/borrow", tags=["Actions"])
def borrow_book_endpoint(book_copy_id: int, reader_id: int, days: int = 14, db: Session = Depends(get_db)):
    try:
        new_loan = services.create_loan(db, book_copy_id, reader_id, days)
        return {"message": "Книгу видано успішно", "loan_id": new_loan.id, "due_date": new_loan.due_date}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/loans/return", tags=["Actions"])
def return_book_endpoint(book_copy_id: int, db: Session = Depends(get_db)):
    try:
        loan = services.return_book(db, book_copy_id)
        return {"message": "Книгу повернуто", "returned_at": loan.returned_at}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/readers/{reader_id}", tags=["Actions"])
def delete_reader_endpoint(reader_id: int, db: Session = Depends(get_db)):
    try:
        result = services.delete_reader(db, reader_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))