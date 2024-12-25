import sqlite3
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from be.model.orm import Book
import os

# 构建book.db的完整路径
db_path = os.path.join('fe', 'data', 'book.db')

# 确认文件存在
if not os.path.exists(db_path):
    raise FileNotFoundError(f"数据库文件不存在: {db_path}")

# 连接SQLite数据库
sqlite_conn = sqlite3.connect(db_path)
sqlite_cursor = sqlite_conn.cursor()

# 读取SQLite中的数据
sqlite_cursor.execute('SELECT id, title, author, publisher, original_title, translator, pub_year, pages, price, currency_unit, binding, isbn, author_intro, book_intro, content, tags, picture FROM book')
data = sqlite_cursor.fetchall()

# 连接PostgreSQL数据库
engine = create_engine(
    "postgresql+psycopg2://postgres:Liuxintong598@localhost:5432/bookstore2",
    echo=True
)

DBSession = sessionmaker(bind=engine)
session = DBSession()

# 批量插入数据
try:
    for row in data:
        book = Book(
            id=row[0],
            title=row[1],
            author=row[2],
            publisher=row[3],
            original_title=row[4],
            translator=row[5],
            pub_year=row[6],
            pages=row[7],
            price=row[8],
            currency_unit=row[9],
            binding=row[10],
            isbn=row[11],
            author_intro=row[12],
            book_intro=row[13],
            content=row[14],
            tags=row[15],
            picture=row[16],
            token=None  # token字段初始为空，后续可以通过jieba分词更新
        )
        session.add(book)
    
    session.commit()
    print("数据导入成功！")

except Exception as e:
    session.rollback()
    print(f"导入出错：{str(e)}")

finally:
    session.close()
    sqlite_conn.close()