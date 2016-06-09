import logging

from sqlalchemy import (
    Column, DateTime, Integer,
    Table, ForeignKey,
)
from sqlalchemy.sql import func

from database import Base, db_engine, db_session

logger = logging.getLogger(__name__)


class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, primary_key=True)
    price = Column(Integer, nullable=False, index=True)
    participant_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, index=True,
                        default=func.now())


def create_db():
    Base.metadata.create_all(db_engine)
