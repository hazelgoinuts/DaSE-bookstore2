import jieba
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from be.model.orm_models import Book as BookModel
from typing import Dict, List, Tuple

class BookIndexBuilder:
    def __init__(self):
        # 数据库连接配置
        self.engine = create_engine(
            "postgresql+psycopg2://stu10205501460:Stu10205501460@dase-cdms-2022-pub.pg.rds.aliyuncs.com:5432/stu10205501460",
            max_overflow=0,
            pool_size=10,
            pool_timeout=5,
            pool_recycle=5,
            echo=True
        )
        self.session = sessionmaker(bind=self.engine)()
    
    def get_book_data(self) -> List[Tuple]:
        """获取需要建立索引的图书数据"""
        query = self.session.query(
            BookModel.id, 
            BookModel.title,
            BookModel.author,
            BookModel.tags,
            BookModel.book_intro
        )
        return query.all()
        
    def segment_text(self, text: str) -> str:
        """使用jieba对文本进行分词"""
        return ' '.join(jieba.cut(str(text), cut_all=False))
    
    def process_book(self, book: Tuple) -> Dict[str, str]:
        """处理单本图书的分词"""
        return {
            'id': book[0],
            'title': self.segment_text(book[1]),
            'author': self.segment_text(book[2]),
            'tags': self.segment_text(book[3]), 
            'intro': self.segment_text(book[4])
        }

    def create_index(self):
        """创建搜索索引"""
        books = self.get_book_data()
        processed_books = [self.process_book(book) for book in books]
        
        # 更新token字段，设置不同字段的权重
        update_sql = """
            UPDATE bookstore_book 
            SET token = setweight(to_tsvector('simple', %(title)s), 'A') ||
                       setweight(to_tsvector('simple', %(tags)s), 'B') ||
                       setweight(to_tsvector('simple', %(intro)s), 'C') ||
                       setweight(to_tsvector('simple', %(author)s), 'D')
            WHERE id = %(id)s
        """
        
        # 批量执行更新
        for book in processed_books:
            self.engine.execute(update_sql, book)
        
        # 验证更新结果
        result = self.session.query(BookModel.token).all()
        print("Token field update completed. Sample results:", result[:5])

    def cleanup(self):
        """清理资源"""
        self.session.close()

if __name__ == "__main__":
    indexer = BookIndexBuilder()
    try:
        indexer.create_index()
    finally:
        indexer.cleanup()