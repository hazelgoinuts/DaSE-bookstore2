from be.model import error
from be.model import db_conn
from be.model.orm_models import Store as Store_model,UserStore as UserStore_model,NewOrder as NewOrder_model, NewOrderDetail as NewOrderDetail_model
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_,or_
from datetime import datetime
from datetime import timedelta
import json

class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)

class Seller(db_conn.CheckExist):

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            with self.get_session() as session:

                new_store = Store_model(store_id = store_id, book_id=book_id,book_info=book_json_str,stock_level=stock_level)
                session.add(new_store)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            

            with self.get_session() as session:
                store = session.query(Store_model).filter(and_(Store_model.store_id==store_id ,Store_model.book_id == book_id)).one()
                store.stock_level = store.stock_level+add_stock_level
            
        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            
            with self.get_session() as session:
                new_userstore = UserStore_model(store_id=store_id,user_id=user_id)
                session.add(new_userstore)
                
        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def delivered(self, user_id: str, order_id: str) -> (int, str):
        try:
            row = None
            with self.get_session() as session:
                row = session.query(NewOrder_model.order_id,
                                    NewOrder_model.store_id, NewOrder_model.status).filter(
                    NewOrder_model.order_id == order_id).all()

                if len(row) != 1:
                    return error.error_invalid_order_id(order_id)

            row = row[0]
            store_id = row.store_id
            status = row.status

            # 判断订单的store_id是否是属于该user_id的
            seller = session.query(UserStore_model.user_id).filter(UserStore_model.store_id == store_id).all()
            seller_id = seller[0].user_id
            if user_id != seller_id:
                return error.error_authorization_fail()

            # 检查订单状态为已支付，其他状态不允许收货
            if status == "已支付":
                with self.get_session() as session:
                    row = session.query(NewOrder_model).filter(NewOrder_model.order_id == order_id).all()
                    if len(row) != 1:
                        return error.error_invalid_order_id(order_id)
                    row = row[0]
                    row.status = "已发货"
                    session.add(row)
            else:
                return error.error_status_not_allowed(order_id)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    # 卖家查询商店的订单信息
    # [{order_id,user_id,status,time,detail:{book_id,count,price}}]
    def seller_search(self, user_id: str, store_id: str):
        try:
            with self.get_session() as session:
                rows = session.query(NewOrder_model.order_id, NewOrder_model.user_id,
                                     NewOrder_model.status, NewOrder_model.time).filter(NewOrder_model.store_id == store_id).all()
                if len(rows) == 0:
                    return error.error_store_no_order(store_id) + ("", )
            out = timedelta(seconds=1)  # 设置为1s后未支付取消
            with self.get_session() as session:
                order_list = []
                for row in rows:
                    order_id = row.order_id
                    buyer_id = row.user_id
                    time = json.dumps(row.time, cls=CJsonEncoder)
                    status = row.status
                    if status == "未支付":
                        time_create = row.time  # 创建订单的时间
                        time_now = datetime.now()  # 现在的时间
                        time_delta = time_now - time_create  # 创建订单的时间到现在的时间差
                        if time_delta >= out:  # 删除NewOrder,NewOrderDetail
                            session.query(NewOrder_model).filter(NewOrder_model.order_id == order_id).delete()
                            session.query(NewOrderDetail_model).filter(
                                NewOrderDetail_model.order_id == order_id).delete()
                        else:
                            details = session.query(NewOrderDetail_model).filter(NewOrderDetail_model.order_id == order_id).all()
                            if len(details) == 0:
                                return error.error_invalid_order_id(order_id) + ("", )

                            detail = []
                            for item in details:
                                detail.append({'book_id':item.book_id, 'count':item.count, 'price':item.price})

                            order_list.append({'order_id':order_id, 'user_id':buyer_id, 'time':time, 'status':status, 'detail':detail})
                    else:
                        details = session.query(NewOrderDetail_model).filter(
                            NewOrderDetail_model.order_id == order_id).all()
                        if len(details) == 0:
                            return error.error_invalid_order_id(order_id) + ("",)

                        detail = []
                        for item in details:
                            detail.append({'book_id': item.book_id, 'count': item.count, 'price': item.price})

                        order_list.append({'order_id': order_id, 'user_id': buyer_id, 'time': time, 'status': status,
                                           'detail': detail})

                if not order_list:
                    return error.error_store_no_order(store_id) + ("", )

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", order_list
