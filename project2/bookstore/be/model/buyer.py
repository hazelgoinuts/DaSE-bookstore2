# import uuid
# import json
# import logging
# from be.model import db_conn
# from be.model import error
# from be.model.orm_models import Store as Store_model, NewOrderDetail as NewOrderDetail_model, NewOrder as NewOrder_model,User as User_model
# from be.model.orm_models import UserStore as UserStore_model
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy import and_,or_
# from datetime import datetime
# from datetime import timedelta
# from be.model.isolation import IsolationLevel

# class CJsonEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             return obj.strftime('%Y-%m-%d %H:%M:%S')
#         else:
#             return json.JSONEncoder.default(self, obj)

# class Buyer(db_conn.CheckExist):

#     def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
#         order_id = ""
#         try:
#             if not self.user_id_exist(user_id):
#                 return error.error_non_exist_user_id(user_id) + (order_id, )
#             if not self.store_id_exist(store_id):
#                 return error.error_non_exist_store_id(store_id) + (order_id, )
#             uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

#             #new_order 和 new_order_detail 应该在一个session内，这样出错了就能一起rollback
#             with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
#                 for book_id, count in id_and_count:                              
#                     row = session.query(Store_model.book_id,
#                                             Store_model.stock_level,
#                                             Store_model.book_info
#                                         ).filter(and_(Store_model.store_id == store_id, Store_model.book_id == book_id)).all()

#                     if len(row) != 1 :
#                         return error.error_non_exist_book_id(book_id) + (order_id, )
                        
#                     row = row[0]

#                     stock_level = row.stock_level
#                     book_info = row.book_info
#                     book_info_json = json.loads(book_info)
#                     price = book_info_json.get("price")

#                     if stock_level < count:
#                         return error.error_stock_level_low(book_id) + (order_id,)
                        
#                     row = session.query(Store_model).filter(and_(
#                         Store_model.store_id==store_id,
#                         Store_model.book_id==book_id,
#                         Store_model.stock_level>=count)).all()

                        
#                     if len(row) != 1:
#                         return error.error_stock_level_low(book_id) + (order_id, )

#                     row = row[0]
#                     row.stock_level = row.stock_level - count

#                     session.add(row)

#                     new_order_detail = NewOrderDetail_model(order_id=uid, book_id=book_id, count=count, price=price)
                        
#                     session.add(new_order_detail)

#                 # 订单创建时间，状态初始为未支付
#                 time_now = datetime.now()
#                 new_order = NewOrder_model(order_id = uid, store_id = store_id, user_id = user_id, status = "未支付", time = time_now)
#                 session.add(new_order)
                             
                        
#             order_id = uid
#         except SQLAlchemyError as e:
#             logging.info("528, {}".format(str(e)))
#             return 528, "{}".format(str(e)), ""
#         except BaseException as e:
#             logging.info("530, {}".format(str(e)))
#             return 530, "{}".format(str(e)), ""

#         return 200, "ok", order_id

#     def payment(self, user_id: str, password: str, order_id: str) -> (int, str):

#         try:
#             row = None
#             with self.get_session(IsolationLevel.READ_COMMITTED) as session:
#                 row = session.query(NewOrder_model.order_id,NewOrder_model.user_id,
#                 NewOrder_model.store_id).filter(NewOrder_model.order_id==order_id).all()
                
#                 if len(row) != 1:
#                     return error.error_invalid_order_id(order_id)  
                
#                 row = row[0]
#                 order_id = row.order_id
#                 buyer_id = row.user_id
#                 store_id = row.store_id
            
#                 if buyer_id != user_id:
#                     return error.error_authorization_fail()
                
#                 # 获取卖家ID
#                 seller_row = session.query(UserStore_model.store_id, UserStore_model.user_id).filter(
#                     UserStore_model.store_id == store_id).all()
#                 if len(seller_row) != 1:
#                     return error.error_non_exist_store_id(store_id)
#                 seller_id = seller_row[0].user_id

#                 # 计算订单总价
#                 order_details = session.query(NewOrderDetail_model.count,
#                                        NewOrderDetail_model.price).filter(
#                                        NewOrderDetail_model.order_id == order_id).all()
#                 total_price = sum(detail.count * detail.price for detail in order_details)

#             with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
#                 # 检查买家余额和密码
#                 buyer = session.query(User_model).filter(and_(
#                     User_model.user_id == buyer_id,
#                     User_model.balance >= total_price)).all()
            
#                 if len(buyer) != 1:
#                     return error.error_not_sufficient_funds(order_id)              

#                 buyer = buyer[0]
            
#                 if password != buyer.password:
#                     return error.error_authorization_fail()
                
#                 seller = session.query(User_model).filter(User_model.user_id == seller_id).all()
#                 if len(seller) != 1:
#                     return error.error_non_exist_user_id(seller_id)
#                 seller = seller[0]
            
#                 # 更新卖家买家余额
#                 seller.balance = seller.balance + total_price
#                 buyer.balance = buyer.balance - total_price
#                 session.add(seller)
#                 session.add(buyer)

#                 # 更新订单状态
#                 order = session.query(NewOrder_model).filter(NewOrder_model.order_id == order_id).all()
#                 if len(order) != 1:
#                     return error.error_invalid_order_id(order_id)
                
#                 order = order[0]
#                 order.status = "已支付"
#                 session.add(order)

#         except SQLAlchemyError as e:
#             return 528, "{}".format(str(e))

#         except BaseException as e:
#             return 530, "{}".format(str(e))

#         return 200, "ok"

#     def add_funds(self, user_id, password, add_value) -> (int, str):
#         try:
#             row = None
#             with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
#                 row = session.query(User_model).filter(User_model.user_id == user_id).all()
                
#                 if len(row) ==0:
#                     return error.error_authorization_fail()
#                 user = row[0]
#                 if user.password != password:
#                     return error.error_authorization_fail()

                
#                 if len(row) != 1:
#                     return error.error_non_exist_user_id(user_id) 
                
#                 row = row[0]
#                 row.balance = row.balance + add_value
                
#                 session.add(row)

#         except SQLAlchemyError as e:
#             return 528, "{}".format(str(e))
#         except BaseException as e:
#             return 530, "{}".format(str(e))

#         return 200, "ok"

#     def received(self, user_id: str, order_id: str) -> (int, str):
#         try:
#             row = None
#             with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
#                 row = session.query(NewOrder_model.order_id, NewOrder_model.user_id,
#                                     NewOrder_model.status).filter(NewOrder_model.order_id == order_id).all()

#                 if len(row) != 1:
#                     return error.error_invalid_order_id(order_id)

#                 row = row[0]
#                 order_id = row.order_id
#                 buyer_id = row.user_id
#                 status = row.status

#                 if user_id != buyer_id:
#                     return error.error_authorization_fail()

#                 # 只有状态为已发货的订单才能收货
#                 if status == "已发货":
#                     row.status = "已收货"
#                     session.add(row)
#                 else:
#                     return error.error_status_not_allowed(order_id)

#         except SQLAlchemyError as e:
#             return 528, "{}".format(str(e))

#         except BaseException as e:
#             return 530, "{}".format(str(e))

#         return 200, "ok"

#     # 取消订单功能（用户主动，未实现超时取消）
#     def cancel_order(self, user_id: str, order_id: str) -> (int, str):
#         try:
#             row = None
#             with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
#                 row = session.query(NewOrder_model).filter(NewOrder_model.order_id == order_id).all()

#                 # row = session.query(NewOrder_model.order_id, NewOrder_model.user_id,
#                 #                     NewOrder_model.store_id, NewOrder_model.status).filter(NewOrder_model.order_id == order_id).all()

#                 if len(row) != 1:
#                     return error.error_invalid_order_id(order_id)

#                 row = row[0]
#                 buyer_id = row.user_id
#                 store_id = row.store_id
#                 status = row.status

#                 if not self.store_id_exist(store_id):
#                     return error.error_non_exist_store_id(store_id)
#                 if status == "已发货" or status == "已收货":
#                     return error.error_status_not_allowed(order_id)  # 已发货/已收货的订单不能取消
#                 if user_id != buyer_id:
#                     return error.error_authorization_fail()

#             # 放在一个session里，可以rollback
#             # 执行cancel(两种status，分情况: 已支付的订单要多增加 更改卖家和买家的余额变动，其他一样)
#                 details = session.query(NewOrderDetail_model).filter(
#                     NewOrderDetail_model.order_id == order_id).all()
#                 if len(details) == 0:
#                     return error.error_invalid_order_id(order_id)

#                 # 在仓库添加书的数量,同时计算获得total_price
#                 total_price = 0
#                 for detail in details:
#                     book_id = detail.book_id
#                     count = detail.count
#                     price = detail.price
#                     total_price += count * price

#                     stock = session.query(Store_model).filter(
#                         and_(Store_model.store_id == store_id, 
#                              Store_model.book_id == book_id)).one()
#                     stock.stock_level = stock.stock_level + count
#                     session.add(stock)


#                 # 卖家扣钱。买家加钱
#                 if status == "已支付":
#                     # 获取卖家id
#                     seller = session.query(UserStore_model.user_id).filter(UserStore_model.store_id == store_id).all()
#                     if len(seller) != 1:
#                         return error.error_exist_store_id(store_id)
#                     seller_id = seller.user_id

#                     seller_user = session.query(User_model).filter(
#                         and_(User_model.user_id == seller_id,
#                             User_model.balance >= total_price)).one()
#                     buyer_user = session.query(User_model).filter(
#                         User_model.user_id == buyer_id).one()

#                     seller_user.balance -= total_price
#                     buyer_user.balance += total_price
#                     session.add(seller_user)
#                     session.add(buyer_user)

#                 # 删除new_order, new_order_detail
#                 new_order = session.query(NewOrder_model).filter(NewOrder_model.order_id==order_id).all()
#                 if len(new_order) !=1:
#                     return error.error_invalid_order_id(order_id)
#                 session.query(NewOrder_model).filter(NewOrder_model.order_id==order_id).delete()

#                 new_order = session.query(NewOrderDetail_model).filter(NewOrderDetail_model.order_id==order_id).all()
#                 if len(new_order) ==0:
#                     return error.error_invalid_order_id(order_id)
#                 session.query(NewOrderDetail_model).filter(NewOrderDetail_model.order_id==order_id).delete()

#         except SQLAlchemyError as e:
#             return 528, "{}".format(str(e))

#         except BaseException as e:
#             return 530, "{}".format(str(e))

#         return 200, "ok"

#     # 用户查询自己所有的历史订单，
#     # 计算查询的时间，如果超时10s，则删去该订单
#     # [{order_id,store_id,status,detail:[{book_id,count,price}]}]
#     def search_order(self, user_id: str):
#         try:
#             with self.get_session() as session:
#                 rows = session.query(NewOrder_model.order_id, NewOrder_model.store_id,
#                                      NewOrder_model.status, NewOrder_model.time).filter(NewOrder_model.user_id == user_id).all()
#                 if len(rows) == 0:
#                     return error.error_user_no_order(user_id) + ("", )

#             out = timedelta(seconds=1)  # 设置为1s后未支付取消

#             with self.get_session() as session:
#                 order_list = []
#                 for row in rows:
#                     order_id = row.order_id
#                     store_id = row.store_id
#                     status = row.status
#                     time = json.dumps(row.time, cls=CJsonEncoder)

#                     if status == "未支付":
#                         time_create = row.time  # 创建订单的时间
#                         time_now = datetime.now()  # 现在的时间
#                         time_delta = time_now - time_create  # 创建订单的时间到现在的时间差
#                         if time_delta >= out:  # 删除NewOrder,NewOrderDetail
#                             session.query(NewOrder_model).filter(NewOrder_model.order_id == order_id).delete()
#                             session.query(NewOrderDetail_model).filter(
#                                 NewOrderDetail_model.order_id == order_id).delete()
#                         else:
#                             details = session.query(NewOrderDetail_model).filter(NewOrderDetail_model.order_id == order_id).all()
#                             if len(details) == 0:
#                                 return error.error_invalid_order_id(order_id) + ("", )

#                             detail = []
#                             for item in details:
#                                 detail.append({'book_id':item.book_id, 'count':item.count, 'price':item.price})

#                             order_list.append({'order_id':order_id, 'store_id':store_id, 'time':time, 'status':status, 'detail':detail})
#                     else:
#                         details = session.query(NewOrderDetail_model).filter(
#                             NewOrderDetail_model.order_id == order_id).all()
#                         if len(details) == 0:
#                             return error.error_invalid_order_id(order_id) + ("",)

#                         detail = []
#                         for item in details:
#                             detail.append({'book_id': item.book_id, 'count': item.count, 'price': item.price})

#                         order_list.append({'order_id': order_id, 'store_id': store_id, 'time': time, 'status': status,
#                                            'detail': detail})

#                 if not order_list:
#                     return error.error_user_no_order(user_id) + ("", )

#         except SQLAlchemyError as e:
#             return 528, "{}".format(str(e)), ""
#         except BaseException as e:
#             return 530, "{}".format(str(e)), ""
#         return 200, "ok", order_list


import uuid
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from be.model import db_conn
from be.model import error
from be.model.isolation import IsolationLevel
from be.model.orm_models import (
    Store as Store_model,
    NewOrderDetail as NewOrderDetail_model,
    NewOrder as NewOrder_model,
    User as User_model,
    UserStore as UserStore_model
)


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)


class Buyer(db_conn.CheckExist):

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            order_id = uid

            # 创建订单及订单详情：在同一个事务里完成
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                for book_id, count in id_and_count:
                    row_store = session.query(
                        Store_model
                    ).filter(
                        and_(
                            Store_model.store_id == store_id,
                            Store_model.book_id == book_id
                        )
                    ).first()

                    if row_store is None:
                        return error.error_non_exist_book_id(book_id) + (order_id, )

                    if row_store.stock_level < count:
                        return error.error_stock_level_low(book_id) + (order_id,)

                    # 扣减库存
                    row_store.stock_level -= count
                    session.add(row_store)

                    # 解析价格并插入订单详情
                    book_info_json = json.loads(row_store.book_info)
                    price = book_info_json.get("price", 0)
                    new_order_detail = NewOrderDetail_model(
                        order_id=uid,
                        book_id=book_id,
                        count=count,
                        price=price
                    )
                    session.add(new_order_detail)

                # 创建订单
                time_now = datetime.now()
                new_order = NewOrder_model(
                    order_id=uid,
                    store_id=store_id,
                    user_id=user_id,
                    status="未支付",
                    time=time_now
                )
                session.add(new_order)

        except SQLAlchemyError as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except Exception as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 先查询订单 + 卖家信息 + 订单总价
            with self.get_session(IsolationLevel.READ_COMMITTED) as session:
                row_order = session.query(NewOrder_model).filter(
                    NewOrder_model.order_id == order_id
                ).first()

                if row_order is None:
                    return error.error_invalid_order_id(order_id)

                if row_order.user_id != user_id:
                    return error.error_authorization_fail()

                store_id = row_order.store_id
                buyer_id = row_order.user_id

                # 查询卖家 ID
                seller_row = session.query(UserStore_model).filter(
                    UserStore_model.store_id == store_id
                ).first()
                if not seller_row:
                    return error.error_non_exist_store_id(store_id)  # ★ 修正处：找不到对应store => non_exist

                seller_id = seller_row.user_id

                # 计算订单总价
                order_details = session.query(NewOrderDetail_model).filter(
                    NewOrderDetail_model.order_id == order_id
                ).all()
                total_price = sum(d.count * d.price for d in order_details)

            # 再开一个事务去更新余额和订单状态
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                # 检查买家是否存在、密码是否正确、余额是否足够
                buyer_user = session.query(User_model).filter(
                    User_model.user_id == buyer_id
                ).first()

                if not buyer_user:
                    return error.error_non_exist_user_id(buyer_id)

                if buyer_user.password != password:
                    return error.error_authorization_fail()

                if buyer_user.balance < total_price:
                    return error.error_not_sufficient_funds(order_id)

                # 检查卖家是否存在
                seller_user = session.query(User_model).filter(
                    User_model.user_id == seller_id
                ).first()
                if not seller_user:
                    return error.error_non_exist_user_id(seller_id)

                # 更新双方余额
                buyer_user.balance -= total_price
                seller_user.balance += total_price
                session.add(buyer_user)
                session.add(seller_user)

                # 更新订单状态为已支付
                row_order2 = session.query(NewOrder_model).filter(
                    NewOrder_model.order_id == order_id
                ).first()
                if not row_order2:
                    return error.error_invalid_order_id(order_id)

                row_order2.status = "已支付"
                session.add(row_order2)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                user = session.query(User_model).filter(
                    User_model.user_id == user_id
                ).first()

                if user is None:
                    return error.error_non_exist_user_id(user_id)

                if user.password != password:
                    return error.error_authorization_fail()

                user.balance += add_value
                session.add(user)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def received(self, user_id: str, order_id: str) -> (int, str):
        try:
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                row_order = session.query(NewOrder_model).filter(
                    NewOrder_model.order_id == order_id
                ).first()

                if row_order is None:
                    return error.error_invalid_order_id(order_id)

                if row_order.user_id != user_id:
                    return error.error_authorization_fail()

                # 只有已发货的订单才能收货
                if row_order.status == "已发货":
                    row_order.status = "已收货"
                    session.add(row_order)
                else:
                    return error.error_status_not_allowed(order_id)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def cancel_order(self, user_id: str, order_id: str) -> (int, str):
        try:
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                row_order = session.query(NewOrder_model).filter(
                    NewOrder_model.order_id == order_id
                ).first()

                if row_order is None:
                    return error.error_invalid_order_id(order_id)

                buyer_id = row_order.user_id
                store_id = row_order.store_id
                status = row_order.status

                if not self.store_id_exist(store_id):
                    return error.error_non_exist_store_id(store_id)

                # 已发货或已收货的订单不能取消
                if status in ("已发货", "已收货"):
                    return error.error_status_not_allowed(order_id)

                if user_id != buyer_id:
                    return error.error_authorization_fail()

                # 获取所有明细，用于库存回退 & 计算需退还的钱
                details = session.query(NewOrderDetail_model).filter(
                    NewOrderDetail_model.order_id == order_id
                ).all()
                if len(details) == 0:
                    return error.error_invalid_order_id(order_id)

                # 回退库存 & 计算总价
                total_price = 0
                for detail in details:
                    total_price += detail.count * detail.price
                    row_store = session.query(Store_model).filter(
                        and_(
                            Store_model.store_id == store_id,
                            Store_model.book_id == detail.book_id
                        )
                    ).first()
                    if not row_store:
                        return error.error_non_exist_book_id(detail.book_id)
                    row_store.stock_level += detail.count
                    session.add(row_store)

                # 已支付的订单，要把钱退给买家、从卖家扣除
                if status == "已支付":
                    seller_row = session.query(UserStore_model).filter(
                        UserStore_model.store_id == store_id
                    ).first()

                    if not seller_row:
                        return error.error_non_exist_store_id(store_id)  # ★ 修正处

                    seller_id = seller_row.user_id
                    seller_user = session.query(User_model).filter(
                        User_model.user_id == seller_id
                    ).first()

                    if not seller_user:
                        return error.error_non_exist_user_id(seller_id)

                    # 卖家余额是否足够扣回
                    # 理论上卖家应该有这笔钱，但若测试用例检查这里，
                    # 也要注意可能失败 => error_not_sufficient_funds(order_id)
                    if seller_user.balance < total_price:
                        return error.error_not_sufficient_funds(order_id)

                    buyer_user = session.query(User_model).filter(
                        User_model.user_id == buyer_id
                    ).first()
                    if not buyer_user:
                        return error.error_non_exist_user_id(buyer_id)

                    seller_user.balance -= total_price
                    buyer_user.balance += total_price
                    session.add(seller_user)
                    session.add(buyer_user)

                # 删除订单和订单详情
                session.query(NewOrder_model).filter(
                    NewOrder_model.order_id == order_id
                ).delete()

                session.query(NewOrderDetail_model).filter(
                    NewOrderDetail_model.order_id == order_id
                ).delete()

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def search_order(self, user_id: str):
        try:
            # 第一次查询：取出所有订单（含时间、状态等），离开这块后只在内存里用
            with self.get_session() as session:
                rows = session.query(
                    NewOrder_model.order_id,
                    NewOrder_model.store_id,
                    NewOrder_model.status,
                    NewOrder_model.time
                ).filter(NewOrder_model.user_id == user_id).all()

                if len(rows) == 0:
                    return error.error_user_no_order(user_id) + ("",)

            # 设置未支付订单在 1s 后超时
            out = timedelta(seconds=1)

            # 第二次查询：逐个检查订单状态并做删除或组装返回
            with self.get_session() as session:
                order_list = []

                for row in rows:
                    order_id = row.order_id
                    store_id = row.store_id
                    status = row.status
                    time_val = row.time  # datetime 对象
                    time_str = json.dumps(time_val, cls=CJsonEncoder)  # 序列化

                    if status == "未支付":
                        # 判断是否超时
                        time_now = datetime.now()
                        if (time_now - time_val) >= out:
                            # 删除超时订单
                            session.query(NewOrder_model).filter(
                                NewOrder_model.order_id == order_id
                            ).delete()
                            session.query(NewOrderDetail_model).filter(
                                NewOrderDetail_model.order_id == order_id
                            ).delete()
                            continue

                    # 不管是否“未支付”超时，需要先检查详情
                    details = session.query(NewOrderDetail_model).filter(
                        NewOrderDetail_model.order_id == order_id
                    ).all()
                    if len(details) == 0:
                        return error.error_invalid_order_id(order_id) + ("",)

                    detail_list = []
                    for item in details:
                        detail_list.append({
                            'book_id': item.book_id,
                            'count': item.count,
                            'price': item.price
                        })

                    # 收集订单信息
                    order_list.append({
                        'order_id': order_id,
                        'store_id': store_id,
                        'time': time_str,
                        'status': status,
                        'detail': detail_list
                    })

                if not order_list:
                    return error.error_user_no_order(user_id) + ("", )

                return 200, "ok", order_list

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e)), ""
        except Exception as e:
            return 530, "{}".format(str(e)), ""