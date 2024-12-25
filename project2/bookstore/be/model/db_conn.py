from be.model import store
from be.model.orm_models import User as User_model, Store as Store_model, UserStore as UserStore_model
from sqlalchemy import and_,or_
from be.model.isolation import IsolationLevel

import logging
logger = logging.getLogger(__name__)

class CheckExist:


    def get_session(self, isolation_level=None):

        return store.get_db_conn(isolation_level)

    
    def user_id_exist(self, user_id):
        with self.get_session() as session:
            row = session.query(User_model.password).filter(User_model.user_id==user_id).all()
            return len(row) != 0


    def book_id_exist(self, store_id, book_id):

        with self.get_session() as session:
            row = session.query(Store_model.book_id).filter(and_(Store_model.store_id==store_id ,Store_model.book_id==book_id)).all()

            if len(row) == 0:
                return False
            else:
                return True
        

    def store_id_exist(self, store_id):

        with self.get_session() as session:
            row = session.query(UserStore_model.store_id).filter(UserStore_model.store_id==store_id).all()

            if len(row) == 0:
                return False
            else:
                return True
