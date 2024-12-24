import random
from fe.access import book
from fe.access.new_seller import register_new_seller
import uuid

class AddStoreBook:
    def __init_store_list__(self):
        self.store_id_list = []

    def __init__(self, store_id):
        self.__init_store_list__()
        self.user_id = "test_seller_id_{}".format(str(uuid.uuid1()))
        self.password = self.user_id
        self.seller = register_new_seller(self.user_id, self.password)
        if store_id != "": #店铺内
            self.store_id = store_id
            code = self.seller.create_store(store_id)
            assert code == 200
        else: #全站
            self.store_id_num = random.randint(5, 20)
            for i in range(self.store_id_num):
                self.store_id_list.append(str(uuid.uuid1()))
                code = self.seller.create_store(self.store_id_list[i])
                assert code == 200

    def add(self, max_book_count: int = 100):
        ok = True
        book_db = book.BookDB()
        rows = book_db.get_book_count()

        if  self.store_id_list == []: #店铺内
            start = 0
            if rows > max_book_count:
                start = random.randint(0, rows - max_book_count)
            size = random.randint(1, max_book_count)
            books = book_db.get_book_info(start, size)
            for bk in books:
                stock_level = random.randint(0, 100)
                code = self.seller.add_book(self.store_id, stock_level, bk)
                assert code == 200
        else: #全站
            for i in range(self.store_id_num):
                start = 0
                if rows > max_book_count:
                    start = random.randint(0, rows - max_book_count)
                size = random.randint(1, max_book_count)
                books = book_db.get_book_info(start, size)
                for bk in books:
                    stock_level = random.randint(0, 100)
                    code = self.seller.add_book(self.store_id_list[i], stock_level, bk)
                    assert code == 200

        return ok

