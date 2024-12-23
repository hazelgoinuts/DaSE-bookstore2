from typing import Tuple, List, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, and_
from sqlalchemy.sql import func
from be.model import error
from be.model import db_conn
from be.model.orm_models import Store as Store_model
from be.model.orm_models import Book as Book_model

class SearchResult:
    def __init__(self, total_pages: int, records: List, current_page_items: List):
        self.total_pages = total_pages
        self.all_records = records
        self.current_page = current_page_items

class Searcher(db_conn.CheckExist):
    PAGE_SIZE = 5  # 每页显示的数量

    def __init__(self):
        super().__init__()

    def _build_search_subquery(self, keyword: str, session):
        """构建搜索子查询，计算相关性得分"""
        return session.query(
            Book_model.title,
            func.ts_rank(Book_model.token, 
                        func.to_tsquery('simple', keyword)).label('search_score')
        ).filter(
            Book_model.token.op('@@')(func.to_tsquery('simple', keyword))
        ).subquery()

    def _build_main_query(self, subquery, store_id: str, session):
        """构建主查询"""
        query = session.query(
            Book_model.title, Book_model.author, Book_model.publisher,
            Book_model.translator, Book_model.author_intro,
            Book_model.book_intro, Book_model.tags
        ).join(
            Store_model, Store_model.book_id == Book_model.id
        ).filter(
            Store_model.stock_level > 0
        ).filter(
            Book_model.title == subquery.c.title
        ).order_by(desc(subquery.c.search_score))

        if store_id:  # 店铺内搜索
            query = query.filter(Store_model.store_id == store_id)
            
        return query

    def _paginate_results(self, results: List, page: int = 1) -> SearchResult:
        """对结果进行分页"""
        total_items = len(results)
        total_pages = (total_items + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        
        start_idx = (page - 1) * self.PAGE_SIZE
        end_idx = min(start_idx + self.PAGE_SIZE, total_items)
        
        current_page_items = results[start_idx:end_idx]
        return SearchResult(total_pages, results, current_page_items)

    def search(self, user_id: str, store_id: str, keyword: str) -> Tuple[int, str, Optional[SearchResult]]:
        """执行搜索"""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (None,)

            if store_id and not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (None,)

            with self.get_session() as session:
                # 构建并执行查询
                subquery = self._build_search_subquery(keyword, session)
                query = self._build_main_query(subquery, store_id, session)
                results = query.all()

                if not results:
                    return error.error_non_exist_search() + (None,)

                # 处理分页
                search_result = self._paginate_results(results)
                return 200, "ok", search_result

        except SQLAlchemyError as e:
            return 528, f"Database error: {str(e)}", None
        except Exception as e:
            return 530, f"Internal error: {str(e)}", None

    def show_page(self, user_id: str, page: int, results: List) -> Tuple[int, str, Optional[SearchResult]]:
        """显示指定页的搜索结果"""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (None,)

            search_result = self._paginate_results(results, page)
            return 200, "ok", search_result

        except SQLAlchemyError as e:
            return 528, f"Database error: {str(e)}", None
        except Exception as e:
            return 530, f"Internal error: {str(e)}", None