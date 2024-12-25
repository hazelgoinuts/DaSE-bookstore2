# be/model/searcher.py
import jieba
from typing import Tuple, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, and_, func
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
    PAGE_SIZE = 5

    def __init__(self):
        super().__init__()

    def _build_search_subquery(self, keyword: str, session):
        """
        先对keyword做jieba分词 => "美丽", "心灵" => "美丽 & 心灵"
        然后用to_tsquery('simple', ...)进行匹配
        """
        # ★ 1. 用jieba分词
        seg_list = list(jieba.cut(keyword, cut_all=False))  # ["美丽", "心灵"]
        # 防止 seg_list 为空或只有空字符
        seg_list = [s.strip() for s in seg_list if s.strip()]
        if not seg_list:
            seg_list = [keyword]

        # ★ 2. 拼接 => "美丽 & 心灵"
        search_str = " & ".join(seg_list)

        # ★ 3. 构建子查询: (title, search_score)
        return session.query(
            Book_model.title,
            func.ts_rank(
                Book_model.token,
                func.to_tsquery('simple', search_str)
            ).label('search_score')
        ).filter(
            Book_model.token.op('@@')(func.to_tsquery('simple', search_str))
        ).subquery()
    
    def _build_main_query(self, subquery, store_id: str, session):
        query = session.query(
            Book_model.title, Book_model.author, Book_model.publisher,
            Book_model.translator, Book_model.author_intro,
            Book_model.book_intro, Book_model.tags
        ).join(
            Store_model, Store_model.book_id == Book_model.id
        ).filter(Store_model.stock_level > 0) \
         .filter(Book_model.title == subquery.c.title) \
         .order_by(desc(subquery.c.search_score))

        if store_id:
            query = query.filter(Store_model.store_id == store_id)
        return query

    def _paginate_results(self, results: List, page: int = 1) -> SearchResult:
        total_items = len(results)
        total_pages = (total_items + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        
        start_idx = (page - 1) * self.PAGE_SIZE
        end_idx = min(start_idx + self.PAGE_SIZE, total_items)
        
        current_page_items = results[start_idx:end_idx]
        return SearchResult(total_pages, results, current_page_items)

    def search(self, user_id: str, store_id: str, keyword: str, is_test: bool = True) -> Tuple[int, int, List, List]:
        try:
            # 1. 校验用户
            if not self.user_id_exist(user_id):
                code, msg = error.error_non_exist_user_id(user_id)
                return code, 0, [], []

            # 2. 校验店铺(若store_id非空，则需存在)
            if store_id and not self.store_id_exist(store_id):
                code, msg = error.error_non_exist_store_id(store_id)
                return code, 0, [], []

            with self.get_session() as session:
                # 3. 构建子查询 (做分词 & tsquery)
                subquery = self._build_search_subquery(keyword, session)
                main_query = self._build_main_query(subquery, store_id, session)
                results = main_query.all()

                # 4. 没有结果 => 返回 522
                if not results:
                    code, msg = error.error_non_exist_search()  # => (522, "non exist query result")
                    return code, 0, [], []

                # 5. 分页(默认page=1)
                sr = self._paginate_results(results, page=1)
                pagenum = sr.total_pages
                row = sr.all_records
                show = sr.current_page
                return 200, pagenum, row, show

        except SQLAlchemyError as e:
            import traceback
            print("SQLAlchemyError caught in search() ", str(e))
            traceback.print_exc()
            return 528, 0, [], []
        except Exception as e:
            return 530, 0, [], []

    def show_page(self, user_id: str, page: int, results: List) -> Tuple[int, int, List, List]:
        try:
            if not self.user_id_exist(user_id):
                code, msg = error.error_non_exist_user_id(user_id)
                return code, 0, [], []

            sr = self._paginate_results(results, page=page)
            pagenum = sr.total_pages
            row = sr.all_records
            show = sr.current_page
            return 200, pagenum, row, show

        except SQLAlchemyError:
            return 528, 0, [], []
        except Exception:
            return 530, 0, [], []