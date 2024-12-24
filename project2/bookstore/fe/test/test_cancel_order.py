import pytest

from fe import conf
from fe.access.buyer import Buyer
from fe.access.book import Book
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
import uuid

class TestCancelOrder:

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

        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                self.total_price = self.total_price + book.price * num

        self.seller = gen_book.seller

        yield

    def test_unpaid_ok(self):
        code = self.buyer.cancel_order(self.order_id)
        assert code == 200

    def test_paid_ok(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.order_id)
        assert code == 200

    def test_error_delivered_received(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.seller.delivered(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.order_id)
        assert code != 200
        code = self.buyer.received(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.order_id)
        assert code != 200

    def test_error_order(self):
        code = self.buyer.cancel_order(self.order_id+'_x')
        assert code != 200

    def test_error_repeat(self):
        code = self.buyer.cancel_order(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.order_id)
        assert code != 200

    def test_error_user_id(self):
        self.buyer.user_id = self.buyer.user_id + '_x'
        code = self.buyer.cancel_order(self.order_id)
        assert code != 200

    def test_error_seller_no_funds(self):
        s = Buyer(conf.URL, user_id = self.seller_id, password = self.seller_id)
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = s.add_funds(-self.total_price-100000)
        assert code == 200
        code = self.buyer.cancel_order(self.order_id)
        assert code != 200
