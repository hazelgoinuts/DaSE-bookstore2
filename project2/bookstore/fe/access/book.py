import os
import random
import base64
#import simplejson as json
from be.model import db_conn
from be.model.orm_models import Book as Book_model
from sqlalchemy import func


class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: [str]
    pictures: [bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB(db_conn.CheckExist):

    def get_book_count(self):

        with self.get_session() as session:
            row = session.query(func.count(Book_model.id).label("count")).one()

            return row.count

    def get_book_info(self, start, size) -> [Book]:
        books = []
        with self.get_session() as session:
            rows = session.query(Book_model.id,
            Book_model.title,Book_model.author,Book_model.publisher,
            Book_model.original_title,Book_model.translator,
            Book_model.pub_year,Book_model.pages,
            Book_model.price,Book_model.currency_unit,Book_model.binding,
            Book_model.isbn,Book_model.author_intro,
            Book_model.book_intro,Book_model.content,
            Book_model.tags,Book_model.picture
            ).order_by(Book_model.id.asc()).offset(start).limit(size)

            for row in rows:
                book = Book()
                book.id = row.id
                book.title = row.title
                book.author = row.author
                book.publisher = row.publisher
                book.original_title = row.original_title
                book.translator = row.translator
                book.pub_year = row.pub_year
                book.pages = row.pages
                book.price = row.price

                book.currency_unit = row.currency_unit
                book.binding = row.binding 
                book.isbn = row.isbn
                book.author_intro = row.author_intro
                book.book_intro = row.book_intro
                book.content = row.content
                tags = row.tags

                picture = row[16]

                for tag in tags.split("\n"):
                    if tag.strip() != "":
                        book.tags.append(tag)
                for i in range(0, random.randint(0, 9)):
                    if picture is not None:
                        encode_str = base64.b64encode(picture).decode('utf-8')
                        book.pictures.append(encode_str)
                books.append(book)
                # print(tags.decode('utf-8'))

                # print(book.tags, len(book.picture))
                # print(book)
                # print(tags)

        return books


