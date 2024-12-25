import pytest
import threading
import time
from fe.access.new_buyer import register_new_buyer
from fe.test.gen_book_data import GenBook
from be.model.store import Store
from be.model.isolation import IsolationLevel
from be.model.orm_models import Store as Store_model
import uuid

class TestIsolation:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.store = Store()
        self.seller_id = "test_isolation_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_isolation_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_isolation_buyer_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        # 生成测试数据
        self.gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, 
            low_stock_level=False,
            max_book_count=5
        )
        assert ok
        # 保存第一本书的ID用于测试
        self.book_id = buy_book_id_list[0][0]
        yield

    def test_read_committed_isolation(self):
        """测试READ COMMITTED隔离级别下的行为"""
        def update_book_stock():
            with self.store.get_db_session(IsolationLevel.READ_COMMITTED) as session:
                # 更新图书库存
                book = session.query(Store_model).filter(
                    Store_model.store_id == self.store_id,
                    Store_model.book_id == self.book_id
                ).first()
                if book:
                    book.stock_level += 10
                    time.sleep(1)  # 模拟长事务

        # 创建一个更新线程
        update_thread = threading.Thread(target=update_book_stock)
        update_thread.start()

        # 在主线程中读取
        with self.store.get_db_session(IsolationLevel.READ_COMMITTED) as session:
            book = session.query(Store_model).filter(
                Store_model.store_id == self.store_id,
                Store_model.book_id == self.book_id
            ).first()
            
            if book:
                initial_stock = book.stock_level
                # 等待更新线程完成
                update_thread.join()
                
                # 再次读取,应该看到更新后的值
                book = session.query(Store_model).filter(
                    Store_model.store_id == self.store_id,
                    Store_model.book_id == self.book_id
                ).first()
                final_stock = book.stock_level
                
                assert final_stock == initial_stock + 10

    def test_repeatable_read_isolation(self):
        """测试REPEATABLE READ隔离级别下的行为"""
        def update_book_stock():
            with self.store.get_db_session(IsolationLevel.REPEATABLE_READ) as session:
                book = session.query(Store_model).filter(
                    Store_model.store_id == self.store_id,
                    Store_model.book_id == self.book_id
                ).first()
                if book:
                    book.stock_level += 10

        # 在REPEATABLE READ级别下开始事务
        with self.store.get_db_session(IsolationLevel.REPEATABLE_READ) as session:
            book = session.query(Store_model).filter(
                Store_model.store_id == self.store_id,
                Store_model.book_id == self.book_id
            ).first()
            
            if book:
                initial_stock = book.stock_level
                
                # 在另一个线程中更新数据
                update_thread = threading.Thread(target=update_book_stock)
                update_thread.start()
                update_thread.join()
                
                # 再次读取,应该看到相同的值
                book = session.query(Store_model).filter(
                    Store_model.store_id == self.store_id,
                    Store_model.book_id == self.book_id
                ).first()
                repeated_read_stock = book.stock_level
                
                assert repeated_read_stock == initial_stock