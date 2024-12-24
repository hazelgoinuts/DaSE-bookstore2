from fe import conf
from fe.access import searcher, auth


def register_new_searcher(user_id, password) -> searcher.Searcher:
    a = auth.Auth(conf.URL)
    code = a.register(user_id, password)
    assert code == 200
    s = searcher.Searcher(conf.URL, user_id, password)
    return s