import logging
logger = logging.getLogger(__name__)

import json
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from be.model import error
from be.model import db_conn
from be.model.orm_models import (
    Store as Store_model,
    UserStore as UserStore_model,
    NewOrder as NewOrder_model,
    NewOrderDetail as NewOrderDetail_model
)
from be.model.isolation import IsolationLevel


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)


class Seller(db_conn.CheckExist):

    # 添加书籍
    def add_book(self, user_id: str, store_id: str, book_id: str,
                 book_json_str: str, stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # 添加书籍时使用 REPEATABLE READ
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                new_store = Store_model(
                    store_id=store_id,
                    book_id=book_id,
                    book_info=book_json_str,
                    stock_level=stock_level
                )
                session.add(new_store)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 增加库存
    def add_stock_level(self, user_id: str, store_id: str, book_id: str,
                        add_stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # 增加库存使用 REPEATABLE READ
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                store = session.query(Store_model).filter(
                    and_(
                        Store_model.store_id == store_id,
                        Store_model.book_id == book_id
                    )
                ).all()
                if len(store) != 1:
                    return error.error_non_exist_book_id(book_id)

                store = store[0]
                store.stock_level += add_stock_level
                session.add(store)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 创建商店
    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            # 创建商店使用 REPEATABLE READ
            with self.get_session(IsolationLevel.REPEATABLE_READ) as session:
                new_userstore = UserStore_model(store_id=store_id, user_id=user_id)
                session.add(new_userstore)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 卖家发货
    def delivered(self, user_id: str, order_id: str) -> (int, str):
        logger.debug(f"Attempting to deliver order {order_id} for user {user_id}")

        try:
            # 发货使用 READ_COMMITTED
            with self.get_session(IsolationLevel.READ_COMMITTED) as session:
                row = session.query(
                    NewOrder_model.order_id,
                    NewOrder_model.store_id,
                    NewOrder_model.status
                ).filter(NewOrder_model.order_id == order_id).first()

                if not row:
                    return error.error_invalid_order_id(order_id)

                store_id = row.store_id
                status = row.status

                # 检查卖家身份
                seller = session.query(UserStore_model.user_id).filter(
                    UserStore_model.store_id == store_id
                ).first()
                if not seller or seller.user_id != user_id:
                    return error.error_authorization_fail()

                # 检查订单状态（必须是“已支付”才可发货）
                if status != "已支付":
                    return error.error_status_not_allowed(order_id)

                # 更新订单状态为“已发货”
                order = session.query(NewOrder_model).filter(
                    NewOrder_model.order_id == order_id
                ).first()
                if not order:
                    return error.error_invalid_order_id(order_id)

                order.status = "已发货"
                session.add(order)

        except SQLAlchemyError as e:
            logger.error(f"Database error while delivering order {order_id}: {str(e)}")
            return 528, "{}".format(str(e))
        except Exception as e:
            logger.error(f"Unexpected error while delivering order {order_id}: {str(e)}")
            return 530, "{}".format(str(e))

        logger.debug(f"Successfully completed delivery process for order {order_id}")
        return 200, "ok"

    # 卖家查询商店订单信息
    # 返回格式: [ {order_id, user_id, status, time, detail: [{book_id, count, price}, ...]} ]
    def seller_search(self, user_id: str, store_id: str):
        try:
            with self.get_session(IsolationLevel.READ_COMMITTED) as session:
                # 先取出所有订单
                rows = session.query(
                    NewOrder_model.order_id,
                    NewOrder_model.user_id,
                    NewOrder_model.status,
                    NewOrder_model.time
                ).filter(NewOrder_model.store_id == store_id).all()

                if len(rows) == 0:
                    return error.error_store_no_order(store_id) + ("", )

                order_list = []
                out = timedelta(seconds=1)  # 设置为 1s 后仍未支付则取消

                for row in rows:
                    order_id = row.order_id
                    buyer_id = row.user_id
                    status = row.status
                    time_str = json.dumps(row.time, cls=CJsonEncoder)

                    # 如果订单是“未支付”，判断是否已超时
                    if status == "未支付":
                        time_create = row.time
                        time_now = datetime.now()
                        time_delta = time_now - time_create
                        if time_delta >= out:
                            # 删除超时订单
                            session.query(NewOrder_model).filter(
                                NewOrder_model.order_id == order_id
                            ).delete()
                            session.query(NewOrderDetail_model).filter(
                                NewOrderDetail_model.order_id == order_id
                            ).delete()
                            continue

                    # 查询订单详情
                    details = session.query(NewOrderDetail_model).filter(
                        NewOrderDetail_model.order_id == order_id
                    ).all()
                    if len(details) == 0:
                        return error.error_invalid_order_id(order_id) + ("", )

                    # 整理订单详情
                    detail_list = []
                    for item in details:
                        detail_list.append({
                            'book_id': item.book_id,
                            'count': item.count,
                            'price': item.price
                        })

                    order_list.append({
                        'order_id': order_id,
                        'user_id': buyer_id,
                        'time': time_str,
                        'status': status,
                        'detail': detail_list
                    })

                # 如果所有订单都被“清理”掉，则也认为该店铺暂无有效订单
                if not order_list:
                    return error.error_store_no_order(store_id) + ("", )

                return 200, "ok", order_list

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e)), ""
        except Exception as e:
            return 530, "{}".format(str(e)), ""