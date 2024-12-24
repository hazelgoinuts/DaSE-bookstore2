import pytest

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
import uuid

class TestSearchOrder:

    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_payment_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_payment_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_payment_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id

        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b
        code, self.order_id = b.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        self.seller = gen_book.seller

        yield

    def test_buyer_search(self):
        code, _ = self.buyer.search_order()
        assert code == 200
        code = self.buyer.cancel_order(self.order_id)
        assert code == 200

    def test_error_no_order(self):
        self.buyer.user_id = self.buyer.user_id + '_x'
        code = self.buyer.search_order()
        assert code != 200

    def test_error_no_detail(self):
        code, order_id = self.buyer.new_order(self.store_id, [])
        assert code == 200
        code = self.buyer.search_order()
        assert code != 200


