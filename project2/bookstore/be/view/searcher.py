from typing import Tuple, List
from flask import Blueprint, request, jsonify
import json
from be.model.searcher import Searcher

bp_searcher = Blueprint("searcher", __name__, url_prefix="/searcher")

def convert_search_data(rows: List[tuple]) -> Tuple[List, List]:
    """把搜索结果转成前端想要的格式。
       data1 = 所有记录
       data2 = 取前5条，模拟第一页
    """
    data1 = [list(item) for item in rows]        # 全部记录
    data2 = [list(item) for item in rows[:5]]    # 第一页
    return data1, data2

def process_search_result(code: int, pagenum: int, row: List, show: List, is_test: bool = True):
    """
    仅在测试时返回 JSON 字符串 + code
    或在非测试时，返回 HTTP 响应
    """
    message = "ok" if code == 200 else "error"
    if not is_test:
        return jsonify({"message": message}), code

    # 测试模式 => 先把 row/show 转成前端想要的 list
    data1, data2 = convert_search_data(row) if row else ([], [])
    response = {
        "message": message,
        "pagenum": pagenum,
        "row": data1,
        "show": data2
    }
    # 返回字符串和状态码 (pytest 里会解析)
    return json.dumps(response), code

@bp_searcher.route("/search", methods=["POST"])
def search():
    # 从请求体取参数
    search_params = {
        "user_id": request.json.get("user_id", ""),
        "store_id": request.json.get("store_id", ""),
        "keyword": request.json.get("keyword", ""),
    }
    is_test: bool = request.json.get("variable", True)

    se = Searcher()
    code, pagenum, row, show = se.search(**search_params, is_test=is_test)

    return process_search_result(code, pagenum, row, show, is_test)

@bp_searcher.route("/show_pages", methods=["POST"])
def show_pages():
    # 从请求体取参数
    user_id = request.json.get("user_id", "")
    page = request.json.get("page", 1)
    content = request.json.get("content", [])  # 即 row
    is_test: bool = request.json.get("variable", True)

    se = Searcher()
    # show_page(...) => 4 个返回值
    code, pagenum, row, show = se.show_page(user_id, page, content)
    return process_search_result(code, pagenum, row, show, is_test)