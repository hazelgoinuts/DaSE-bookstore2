from typing import Tuple, List, Dict, Any
from flask import Blueprint, request, jsonify
import json
from be.model.searcher import Searcher

bp_searcher = Blueprint("searcher", __name__, url_prefix="/searcher")

def convert_search_data(rows: List[tuple]) -> Tuple[List, List]:
    data1 = [list(item) for item in rows]
    data2 = [list(item) for item in rows[:5]]  # 第一页数据
    return data1, data2

def process_search_result(code: int, message: str, 
                         pagenum: int = None, row: List = None, 
                         show: List = None, is_test: bool = True) -> Tuple[Any, int]:
    if not is_test:
        return jsonify({"message": message}), code
    
    # 处理测试模式的返回
    data1, data2 = convert_search_data(row) if row else ([], [])
    response = {
        "message": message,
        "pagenum": pagenum,
        "row": data1,
        "show": data2
    }
    return json.dumps(response), code

@bp_searcher.route("/search", methods=["POST"])
def search():
    search_params = {
        "user_id": request.json.get("user_id", ""),
        "store_id": request.json.get("store_id", ""),
        "keyword": request.json.get("keyword", ""),
    }
    is_test: bool = request.json.get("variable", True)

    se = Searcher()
    if is_test:
        code, message, pagenum, row, show = se.search(**search_params)
        return process_search_result(code, message, pagenum, row, show, is_test)
    else:
        code, message = se.search(**search_params)
        return process_search_result(code, message, is_test=is_test)

@bp_searcher.route("/show_pages", methods=["POST"])
def show_pages():
    params = {
        "user_id": request.json.get("user_id", ""),
        "page": request.json.get("page", "1"),
        "content": request.json.get("content", [])
    }
    is_test: bool = request.json.get("variable", True)

    se = Searcher()
    if is_test:
        code, message, show, row = se.show_pages(**params)
        response = {
            "message": message,
            "show": [list(item) for item in show] if show else [],
            "row": [list(item) for item in row] if row else []
        }
        return jsonify(response), code
    else:
        code, message = se.search(params["user_id"], params["page"], params["content"])
        return jsonify({"message": message}), code