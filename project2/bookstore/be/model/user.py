import jwt
import time
import logging
from be.model import error
from be.model import db_conn
from be.model.orm_models import User as User_model
from sqlalchemy.exc import SQLAlchemyError

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.encode("utf-8").decode("utf-8")


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.CheckExist):
    token_lifetime: int = 3600  # 3600 second


    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False


    def register(self, user_id: str, password: str):

        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            with self.get_session() as session:

                new_user = User_model(user_id=user_id, password=password, balance=0, token=token, terminal=terminal)
                session.add(new_user)

        except Exception as e:
            return error.error_exist_user_id(user_id)
        return 200, "ok"


    def check_token(self, user_id: str, token: str) -> (int, str):

        with self.get_session() as session:

            row = session.query(User_model.token).filter(User_model.user_id==user_id).all()

        if len(row) !=1 :
            return error.error_authorization_fail()

        db_token = row[0].token

        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"


    def check_password(self, user_id: str, password: str) -> (int, str):

        with self.get_session() as session:

            row = session.query(User_model.password).filter(User_model.user_id==user_id).all()

        if len(row) !=1:
            return error.error_authorization_fail()

        if password != row[0].password:
            return error.error_authorization_fail()

        return 200, "ok"


    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)

            with self.get_session() as session:

                row = session.query(User_model).filter(User_model.user_id==user_id).all()

                if len(row) != 1:
                    return error.error_authorization_fail() + ("", )
            

                user = row[0]

                user.token = token
                user.terminal = terminal
                            
                session.add(user)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token


    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            with self.get_session() as session:

                row = session.query(User_model).filter(User_model.user_id==user_id).all()
                
                if len(row) !=1 :
                    return error.error_authorization_fail() + ("", )
                
                user = row[0]

                user.token = dummy_token
                user.terminal = terminal
                
                session.add(user)

        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            with self.get_session() as session:
                row = session.query(User_model).filter(User_model.user_id==user_id).all()

                if len(row) ==1:
                    user = row[0]
                    session.delete(user)
                else:
                    return error.error_authorization_fail()
        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            with self.get_session() as session:
               
                row = session.query(User_model).filter(User_model.user_id==user_id).all()
                
                if len(row)!=1:
                    return error.error_authorization_fail()

                user = row[0]

                user.password = new_password
                user.token = token
                user.terminal = terminal
                session.add(user)
                
        except SQLAlchemyError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

