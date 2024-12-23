from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import seller
import json

bp_seller = Blueprint("seller", __name__, url_prefix="/seller")


@bp_seller.route("/create_store", methods=["POST"])
def seller_create_store():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    s = seller.Seller()
    code, message = s.create_store(user_id, store_id)
    return jsonify({"message": message}), code


@bp_seller.route("/add_book", methods=["POST"])
def seller_add_book():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_info: str = request.json.get("book_info")
    stock_level: str = request.json.get("stock_level", 0)

    s = seller.Seller()
    code, message = s.add_book(
        user_id, store_id, book_info.get("id"), json.dumps(book_info), stock_level
    )

    return jsonify({"message": message}), code


@bp_seller.route("/add_stock_level", methods=["POST"])
def add_stock_level():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_num: str = request.json.get("add_stock_level", 0)

    s = seller.Seller()
    code, message = s.add_stock_level(user_id, store_id, book_id, add_num)

    return jsonify({"message": message}), code

# 新增的

# 发货
@bp_seller.route("/delivered", methods=["POST"])
def delivered():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")

    s = seller.Seller()
    code, message = s.delivered(user_id, order_id)

    return jsonify({"message": message}), code

# 卖家查询订单
@bp_seller.route("/seller_search", methods=["POST"])
def search_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    s = seller.Seller()
    code, message, rows = s.seller_search(user_id, store_id)
    if not rows:
        print('be: no order content !')
        return jsonify({"message": message, "order_list": rows}), code
    else:
        data = []
        for item in rows:
            a = list(item.values())
            d = []
            for i in a[-1]:
                i = list(i.values())
                d.append(i)
            a[-1] = d
            data.append(a)

        print('be:', data)
        return json.dumps({"order_list": data}), code


