from be.model import store
from be.model.orm_models import User as User_model, Store as Store_model, UserStore as UserStore_model
from sqlalchemy import and_,or_

class CheckExist:


    def get_session(self):
        return store.get_db_conn()

    
    def user_id_exist(self, user_id):

        with self.get_session() as session:
            row = session.query(User_model.password).filter(User_model.user_id==user_id).all()


            if len(row) == 0:
                return False
            else:
                return True


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
