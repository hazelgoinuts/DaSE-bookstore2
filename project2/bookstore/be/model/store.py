from be.model.orm_models import createTable
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from be.model.isolation import IsolationLevel
from contextlib import contextmanager

## 添加日志
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
##

class Store:
    def __init__(self):
        self.engine = create_engine(
            "postgresql+psycopg2://postgres:Liuxintong598@localhost:5432/bookstore2",
            # isolation_level='READ COMMITTED',  # 默认隔离级别
            pool_size=8,
            max_overflow=16,
            pool_recycle=300,
            pool_pre_ping=True,  # 连接池预检查
            echo = True
        )
        self.DBSession = sessionmaker(
            bind=self.engine,
            expire_on_commit=False  # 提交后不过期对象
        )
        self.init_tables()

    def init_tables(self):
        try:
            createTable(self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tables: {e}")
            raise e

    @contextmanager
    def get_db_session(self, isolation_level=None):
        session = scoped_session(self.DBSession)
        try:
            if isolation_level:
                session.connection(execution_options=
                                   {"isolation_level": isolation_level.value})
            yield session
            session.commit()
            logger.debug("Session committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Session error occurred: {e}")
            raise e
        finally:
            session.remove()

database_instance: Store = None

def init_database():
    global database_instance
    database_instance = Store()

def get_db_conn(isolation_level=None):
    global database_instance
    return database_instance.get_db_session(isolation_level)