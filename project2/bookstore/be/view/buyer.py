from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.buyer import Buyer
import json

bp_buyer = Blueprint("buyer", __name__, url_prefix="/buyer")


@bp_buyer.route("/new_order", methods=["POST"])
def new_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    books: [] = request.json.get("books")
    id_and_count = []
    for book in books:
        book_id = book.get("id")
        count = book.get("count")
        id_and_count.append((book_id, count))

    b = Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    return jsonify({"message": message, "order_id": order_id}), code


@bp_buyer.route("/payment", methods=["POST"])
def payment():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    password: str = request.json.get("password")
    b = Buyer()
    code, message = b.payment(user_id, password, order_id)
    return jsonify({"message": message}), code


@bp_buyer.route("/add_funds", methods=["POST"])
def add_funds():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    add_value = request.json.get("add_value")
    b = Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    return jsonify({"message": message}), code

# 新增的

# 收货
@bp_buyer.route("/received", methods=["POST"])
def received():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")
    b = Buyer()
    code, message = b.received(user_id, order_id)
    return jsonify({"message": message}), code

# 取消订单
@bp_buyer.route("/cancel_order", methods=["POST"])
def cancel_order():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")
    b = Buyer()
    code, message = b.cancel_order(user_id, order_id)
    return jsonify({"message": message}), code

# 查询历史订单
@bp_buyer.route("/search_order", methods=["POST"])
def search_order():
    user_id: str = request.json.get("user_id")
    b = Buyer()
    code, message, rows = b.search_order(user_id)
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



