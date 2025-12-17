# Документація реалізованих запитів (SQL)

У цьому розділі наведено опис ключових аналітичних запитів системи. Хоча в програмному коді використовується ORM (SQLAlchemy), нижче наведено їх SQL-еквіваленти, що демонструють структуру вибірки, з'єднання таблиць та логіку агрегації.

---

## Запит 1: Рейтинг читачів (Window Functions)

### Бізнес-питання

**"Як розподілити місця (ранги) між читачами на основі кількості прочитаних книг, враховуючи, що кілька людей можуть мати однаковий результат?"**

Цей запит демонструє використання просунутих можливостей SQL (віконних функцій) для побудови справедливого рейтингу ("Дошка пошани").

### SQL-еквівалент

```sql
SELECT 
    subquery.first_name,
    subquery.last_name,
    subquery.total_loans,
    RANK() OVER (ORDER BY subquery.total_loans DESC) as rank
FROM (
    SELECT 
        r.id,
        r.first_name,
        r.last_name,
        COUNT(l.id) as total_loans
    FROM readers r
    JOIN loans l ON r.id = l.reader_id
    GROUP BY r.id
) as subquery;
```

### Пояснення логіки

* **Підзапит (Subquery):** спочатку агрегуємо дані по кожному читачеві, підраховуючи кількість записів у таблиці `loans` (`COUNT`).
* **Віконна функція `RANK()`:** присвоює порядковий номер кожному рядку на основі стовпця `total_loans`.
* **Особливість:** якщо два читачі прочитали однакову кількість книг, вони отримають однаковий ранг; наступний ранг буде пропущено (наприклад, 1, 1, 3).

### Приклад виводу

| first_name | last_name | total_loans | rank |
| :--------- | :-------- | :---------- | :--- |
| Іван       | Тестовий  | 15          | 1    |
| Марія      | Коваленко | 12          | 2    |
| Петро      | Сидоренко | 12          | 2    |
| Олена      | Бойко     | 5           | 4    |

### Реалізація в проєкті (SQLAlchemy)

```python
def get_reader_ranks(session):
    reader_stats = session.query(
        Reader.id,
        Reader.first_name,
        Reader.last_name,
        func.count(Loan.id).label('total_loans')
    ).join(Loan).group_by(Reader.id).subquery()

    query = session.query(
        reader_stats.c.first_name,
        reader_stats.c.last_name,
        reader_stats.c.total_loans,
        func.rank().over(order_by=desc(reader_stats.c.total_loans)).label('rank')
    )
    
    return query.all()
```

---

## Запит 2: Аналіз популярності жанрів (Multi-Join Aggregation)

### Бізнес-питання

**"Які літературні жанри користуються найбільшим попитом у бібліотеці?"**

Допомагає визначити пріоритети при закупівлі нових книг. Вимагає з'єднання кількох таблиць, щоб пов'язати жанр з фактом видачі книги.

### SQL-еквівалент

```sql
SELECT 
    g.name as genre_name,
    COUNT(l.id) as loan_count
FROM genres g
JOIN books b ON g.id = b.genre_id
JOIN book_copies bc ON b.id = bc.book_id
JOIN loans l ON bc.id = l.book_copy_id
GROUP BY g.name
ORDER BY loan_count DESC;
```

### Пояснення логіки

* **Ланцюжок JOIN:** виконується прохід по схемі: `Genre → Book → BookCopy → Loan`.
* **Агрегація `COUNT`:** підраховує кількість фактів видачі для кожного жанру.
* **Сортування:** від найпопулярнішого до найменш популярного.

### Приклад виводу

| genre_name         | loan_count |
| :----------------- | :--------- |
| Фантастика         | 42         |
| Наукова література | 28         |
| Класика            | 15         |

### Реалізація в проєкті (SQLAlchemy)

```python
def get_genre_popularity(session: Session):

    print(f"Популярність жанрів")

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
```

---

## Запит 3: Звіт про боржників (Date Logic & Filtering)

### Бізнес-питання

**"Хто з читачів не повернув книги вчасно і скільки днів становить прострочення?"**

Критично важливий операційний запит для роботи бібліотекаря.

### SQL-еквівалент

```sql
SELECT 
    r.first_name,
    r.last_name,
    b.title,
    l.due_date,
    (CURRENT_DATE - l.due_date) as days_overdue
FROM loans l
JOIN readers r ON l.reader_id = r.id
JOIN book_copies bc ON l.book_copy_id = bc.id
JOIN books b ON bc.book_id = b.id
WHERE l.returned_at IS NULL 
  AND l.due_date < CURRENT_DATE;
```

### Пояснення логіки

* **Фільтрація `IS NULL`:** відбираємо тільки ті записи, де дата повернення ще не встановлена (книга на руках).
* **Логіка дати:** умова `due_date < CURRENT_DATE` відбирає ті випадки, де дедлайн вже минув.
* **Обчислення:** вираз `(CURRENT_DATE - l.due_date)` динамічно розраховує кількість днів затримки.

### Приклад виводу

| first_name | last_name | title  | due_date   | days_overdue |
| :--------- | :-------- | :----- | :--------- | :----------- |
| Олег       | Петров    | 1984   | 2023-11-01 | 45           |
| Анна       | Сміт      | Кобзар | 2023-12-10 | 5            |

### Реалізація в проєкті (SQLAlchemy)

```python
def get_overdue_loans(session: Session):

    print(f"Звіт: Боржники")
    
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
```

---

## Запит 4: Топ-5 активних читачів (Limit & Group By)

### Бізнес-питання

**"Хто є найактивнішими користувачами бібліотеки?"**

### SQL-еквівалент

```sql
SELECT 
    r.first_name,
    r.last_name,
    COUNT(l.id) as total_books
FROM readers r
JOIN loans l ON r.id = l.reader_id
GROUP BY r.id
ORDER BY total_books DESC
LIMIT 5;
```

### Пояснення логіки

* **GROUP BY r.id:** групування за унікальним ідентифікатором читача, щоб користувачі з однаковими іменами не зливалися в один рядок.
* **LIMIT 5:** відсікає зайві рядки, залишаючи тільки верхівку рейтингу.

### Приклад виводу

| first_name | last_name | total_books |
| :--------- | :-------- | :---------- |
| Іван       | Тестовий  | 15          |
| Марія      | Коваленко | 12          |
| Петро      | Сидоренко | 12          |
| Олена      | Бойко     | 5           |
| Дмитро     | Гнатюк    | 3           |

### Реалізація в проєкті (SQLAlchemy)

```python
def get_top_readers(session: Session):

    print(f"Топ-5 читачів")
    
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
```

---

## Запит 5: Пошук книг за жанром (Filtering & Sorting)

### Бізнес-питання

**"Які книги певного жанру (наприклад, 'Фантастика') є в бібліотеці, починаючи з найновіших?"**

Цей запит є базовим інструментом для читача або бібліотекаря, коли потрібно знайти літературу за певною тематикою.

### SQL-еквівалент

```sql
SELECT 
    b.title,
    b.publication_year,
    g.name as genre
FROM books b
JOIN genres g ON b.genre_id = g.id
WHERE g.name = :genre_name
ORDER BY b.publication_year DESC;
```

### Пояснення логіки

* **JOIN genres:** приєднуємо таблицю жанрів, щоб фільтрувати не за ID, а за зрозумілою назвою (наприклад, 'Фантастика').
* **WHERE:** відсіює книги, що не належать до обраного жанру.
* **ORDER BY ... DESC:** сортування за роком видання у спадному порядку, щоб найновіші видання були першими.

### Приклад виводу (для жанру "Фантастика")

| title        | publication_year | genre      |
| :----------- | :--------------- | :--------- |
| Гаррі Поттер | 1997             | Фантастика |
| Гіперіон     | 1989             | Фантастика |
| Дюна         | 1965             | Фантастика |
| Соляріс      | 1961             | Фантастика |

### Реалізація в проєкті (SQLAlchemy)

```python
def get_books_by_genre(session: Session, genre_name: str):

    print(f"Пошук книг жанру: '{genre_name}'")
    
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
```
