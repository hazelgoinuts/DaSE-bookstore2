from be.model.orm_models import createTable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session
from contextlib import contextmanager


class Store:

    def __init__(self):

        self.engine = create_engine("postgresql+psycopg2://postgres:Liuxintong598@localhost:5432/bookstore2",echo=True)
        self.DBSession = sessionmaker(bind=self.engine)
        self.init_tables()


    def init_tables(self):

        createTable(self.engine)


    @contextmanager
    def get_db_session(self):
        try:
            session = scoped_session(self.DBSession)
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.remove()


database_instance: Store = None


def init_database():
    global database_instance
    database_instance = Store()


def get_db_conn():
    global database_instance
    return database_instance.get_db_session()

if __name__ == "__main__":
    init_database()