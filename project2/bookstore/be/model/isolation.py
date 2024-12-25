from enum import Enum
import logging
from sqlalchemy.exc import SQLAlchemyError

class IsolationLevel(Enum):
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"

class TransactionIsolation:
    def __init__(self, session):
        self.session = session
        # 默认使用READ COMMITTED
        self._isolation_level = IsolationLevel.READ_COMMITTED

    @property
    def isolation_level(self):
        return self._isolation_level

    def set_isolation_level(self, level: IsolationLevel):
        """设置事务隔离级别"""
        try:
            if not isinstance(level, IsolationLevel):
                raise ValueError("Invalid isolation level")
            
            self.session.connection(execution_options={
                "isolation_level": level.value
            })
            self._isolation_level = level
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error setting isolation level: {str(e)}")
            return False