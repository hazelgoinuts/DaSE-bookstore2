import requests
from urllib.parse import urljoin

class Auth:
    def __init__(self, url_prefix):
        # 移除额外的auth/拼接
        self.url_prefix = url_prefix.rstrip('/')
        print(f"Debug - Base URL: {self.url_prefix}")  # debug日志
        
    def register(self, user_id: str, password: str) -> int:
        json = {"user_id": user_id, "password": password}
        url = f"{self.url_prefix}/auth/register"
        print(f"Debug - Request URL: {url}")  # debug日志
        r = requests.post(url, json=json)
        print(f"Debug - Response: {r.status_code}")  # debug日志
        return r.status_code
        
    def login(self, user_id: str, password: str, terminal: str) -> (int, str):
        json = {"user_id": user_id, "password": password, "terminal": terminal}
        url = f"{self.url_prefix}/auth/login"
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("token")

    def password(self, user_id: str, old_password: str, new_password: str) -> int:
        json = {
            "user_id": user_id,
            "oldPassword": old_password,
            "newPassword": new_password,
        }
        url = f"{self.url_prefix}/auth/password"
        r = requests.post(url, json=json)
        return r.status_code

    def logout(self, user_id: str, token: str) -> int:
        json = {"user_id": user_id}
        headers = {"token": token}
        url = f"{self.url_prefix}/auth/logout"
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def unregister(self, user_id: str, password: str) -> int:
        json = {"user_id": user_id, "password": password}
        url = f"{self.url_prefix}/auth/unregister" 
        r = requests.post(url, json=json)
        return r.status_code