import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jieba
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from be.model.orm import Book as book_model

def init_database(engine):
    print("初始化数据库...")
    try:
        with engine.connect() as conn:
            # 添加token字段（如果不存在）
            conn.execute(text("""
                ALTER TABLE book 
                ADD COLUMN IF NOT EXISTS token tsvector;
            """))
            # 创建GIN索引（如果不存在）
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_book_token 
                ON book 
                USING gin(token);
            """))
            print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化错误: {e}")
        raise

def main():
    engine = create_engine(
        "postgresql+psycopg2://postgres:Liuxintong598@localhost:5432/bookstore2",
        max_overflow=0,
        pool_size=10,
        pool_timeout=5,
        pool_recycle=5,
        echo=False
    )

    # 初始化数据库
    init_database(engine)

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    try:
        print("开始获取书籍数据...")
        res = session.query(
            book_model.id, 
            book_model.title, 
            book_model.author, 
            book_model.tags, 
            book_model.book_intro
        ).all()
        print(f"获取到 {len(res)} 本书的数据")

        c_i = []
        c_t = []
        c_a = []
        c_ta = []
        c_b = []

        print("开始分词处理...")
        for i in range(len(res)):
            book_id = res[i][0]
            title_str = str(res[i][1])
            author_str = str(res[i][2])
            tags_str = str(res[i][3])
            book_intro_str = str(res[i][4])

            # 分词
            seg_t = " ".join(jieba.cut(title_str, cut_all=False))
            seg_a = " ".join(jieba.cut(author_str, cut_all=False))
            seg_ta = " ".join(jieba.cut(tags_str, cut_all=False))
            seg_b = " ".join(jieba.cut(book_intro_str, cut_all=False))

            c_i.append(book_id)
            c_t.append(seg_t)
            c_a.append(seg_a)
            c_ta.append(seg_ta)
            c_b.append(seg_b)

        print("开始更新token...")
        update_sql = text("""
        UPDATE book
        SET token = setweight(to_tsvector('simple', :title), 'A')
                  || setweight(to_tsvector('simple', :tags), 'B')
                  || setweight(to_tsvector('simple', :book_intro), 'C')
                  || setweight(to_tsvector('simple', :author), 'D')
        WHERE id = :book_id
        """)

        with engine.connect() as conn:
            for i in range(len(res)):
                conn.execute(update_sql, {
                    'title': c_t[i],
                    'tags': c_ta[i],
                    'book_intro': c_b[i],
                    'author': c_a[i],
                    'book_id': c_i[i]
                })
                if i % 100 == 0:
                    print(f"已处理 {i}/{len(res)} 本书")
            conn.commit()

        print("验证token创建结果...")
        to = session.query(book_model.token).limit(5).all()
        print("Token示例(前5条):")
        for t in to:
            print(t[0])

    except Exception as e:
        print(f"处理过程中出错: {e}")
        raise
    finally:
        session.close()
        print("处理完成")

if __name__ == "__main__":
    main()