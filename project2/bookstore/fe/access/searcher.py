import requests
from urllib.parse import urljoin
from fe.access.auth import Auth
import json
import jieba


# class Searcher:
    # def __init__(self, url_prefix, user_id, password):
    #     self.url_prefix = urljoin(url_prefix, "searcher/")
    #     self.user_id = user_id
    #     self.password = password
    #     self.terminal = "my terminal"
    #     self.auth = Auth(url_prefix)
    #     code, self.token = self.auth.login(self.user_id, self.password, self.terminal)
    #     assert code == 200

    # def search(self, store_id: str, keyword: str, va: bool):
    #     #分词
    #     kw = ' | '.join(jieba.cut(keyword, cut_all=False))

    #     json = {
    #         "user_id": self.user_id,
    #         "store_id": store_id,
    #         "keyword": kw,
    #         "variable": va
    #     }
    #     url = urljoin(self.url_prefix, "search")
    #     headers = {"token": self.token}

    #     r = requests.post(url, headers=headers, json=json)
    #     response_json = r.json()
    #     if va:
    #         return r.status_code, response_json.get("pagenum"), response_json.get("row"), response_json.get("show")
    #     else:
    #         return r.status_code
class Searcher:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = url_prefix.rstrip('/')
        self.user_id = user_id
        self.password = password
        self.terminal = "my terminal"
        self.auth = Auth(url_prefix)
        code, self.token = self.auth.login(self.user_id, self.password, self.terminal)
        assert code == 200
        print(f"Debug - Searcher initialized with URL: {self.url_prefix}")

    def search(self, store_id: str, keyword: str, va: bool):
        try:
            #分词
            kw = ' | '.join(jieba.cut(keyword, cut_all=False))
            print(f"Debug - Search keyword after jieba: {kw}")

            json = {
                "user_id": self.user_id,
                "store_id": store_id,
                "keyword": kw,
                "variable": va
            }
            url = f"{self.url_prefix}/searcher/search"
            headers = {"token": self.token}
            
            r = requests.post(url, headers=headers, json=json)

            print("==================== Debug Info ====================")
            print(f"Debug - Search request URL: {url}")
            print(f"Debug - Search response status: {r.status_code}")
            print(f"Debug - Search response content: {r.text}")
            print("=================================================")


            # if r.status_code != 200:
            #     return r.status_code, None, None, None
                
            # 如果是va模式,需要解析完整的JSON响应
            if va:
                try:
                    response_json = r.json()
                    return (
                        r.status_code,  # code1
                        response_json.get("pagenum", 0),  # pagenum
                        response_json.get("row", []),     # row
                        response_json.get("show", [])     # show (对应测试中的_)
                    )
                except Exception as e:
                    print(f"Debug - JSON parsing failed: {e}")
                    return 500, None, None, None
            # 非va模式只返回状态码
            else:
                return r.status_code
                
        except Exception as e:
            print(f"Debug - Search request failed: {e}")
            return 500, None, None, None

    # def search(self, store_id: str, keyword: str, va: bool):
    #     try:
    #         # 分词
    #         kw = ' | '.join(jieba.cut(keyword, cut_all=False))
    #         print(f"Debug - Search keyword after jieba: {kw}")
            
    #         json = {
    #             "user_id": self.user_id,
    #             "store_id": store_id,
    #             "keyword": kw,
    #             "variable": va
    #         }
    #         url = f"{self.url_prefix}/searcher/search"
    #         headers = {"token": self.token}
            
    #         print("==================== Debug Info ====================")
    #         print(f"Debug - Search request URL: {url}")
    #         print(f"Debug - Request payload: {json}")
            
    #         r = requests.post(url, headers=headers, json=json)
            
    #         print(f"Debug - Search response status: {r.status_code}")
    #         print(f"Debug - Search response content: {r.text}")
    #         print("=================================================")
            
    #         if r.status_code != 200:
    #             print(f"Debug - Request failed with status code: {r.status_code}")
    #             return r.status_code, None, None, None
            
    #         try:
    #             response_json = r.json()
    #         except ValueError as e:
    #             print(f"Debug - Failed to parse JSON response: {e}")
    #             return 500, None, None, None
            
    #         if va:
    #             # 验证响应数据的完整性
    #             if not all(k in response_json for k in ["pagenum", "row", "show"]):
    #                 print("Debug - Response missing required fields")
    #                 return 500, None, None, None
                
    #             return (
    #                 r.status_code,
    #                 response_json.get("pagenum"),
    #                 response_json.get("row"),
    #                 response_json.get("show")
    #             )
    #         else:
    #             return r.status_code
            
    #     except requests.RequestException as e:
    #         print(f"Debug - HTTP request failed: {e}")
    #         return 500, None, None, None
    #     except Exception as e:
    #         print(f"Debug - Unexpected error: {e}")
    #         return 500, None, None, None

    def show_pages(self, page, content, va):
        json = {
            "user_id": self.user_id,
            "page": int(page),
            "content": content,
            "variable": va
        }
        url = urljoin(self.url_prefix, "show_pages")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        if va:
            return r.status_code, response_json.get("pagenum"), response_json.get("row"), response_json.get("show")
        else:
            return r.status_code