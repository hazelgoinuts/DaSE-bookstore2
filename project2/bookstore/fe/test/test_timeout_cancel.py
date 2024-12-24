import pytest

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
import uuid
from time import sleep

class TestTimeOut:

    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_payment_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_payment_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_payment_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id

        yield

    def test_timeout_cancel_buyer(self):
        gen_book1 = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list1 = gen_book1.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        assert ok
        gen_book2 = GenBook(self.seller_id+'_y', self.store_id+'_y')
        ok, buy_book_id_list2 = gen_book2.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        assert ok
        b = register_new_buyer(self.buyer_id, self.password)
        code, order_id1 = b.new_order(self.store_id, buy_book_id_list1)
        assert code == 200
        sleep(2)
        code, order_id2 = b.new_order(self.store_id+'_y', buy_book_id_list2)
        assert code == 200
        code, order_list = b.search_order()
        assert code == 200
        assert len(order_list) == 1

    def test_timeout_no_order_buyer(self):
        gen_book1 = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list1 = gen_book1.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        assert ok
        b = register_new_buyer(self.buyer_id, self.password)
        code, order_id1 = b.new_order(self.store_id, buy_book_id_list1)
        assert code == 200
        sleep(2)
        code, order_list = b.search_order()
        assert code != 200

    def test_timeout_cancel_seller(self):
        gen_book1 = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list1 = gen_book1.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        assert ok
        s = gen_book1.seller
        b = register_new_buyer(self.buyer_id, self.password)
        code, order_id1 = b.new_order(self.store_id, buy_book_id_list1)
        assert code == 200
        sleep(2)
        code = s.seller_search(self.store_id)
        assert code != 200


