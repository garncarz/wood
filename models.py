import logging

from sqlalchemy import (
    Column, Boolean, DateTime, Enum, Integer,
    Table, ForeignKey,
)
from sqlalchemy.sql import func

from database import Base, db_engine, db_session

logger = logging.getLogger(__name__)


class Order(Base):
    __tablename__ = 'order'

    id = Column(Integer, primary_key=True)
    traded = Column(Boolean, default=False, nullable=False, index=True)
    side = Column(Enum('buy', 'sell'), nullable=False, index=True)
    price = Column(Integer, nullable=False, index=True)
    participant_id = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=False)
    registered_at = Column(DateTime, nullable=False, index=True,
                           default=func.now())

    def __repr__(self):
        return '<Order %s/$%d/%d pcs>' % (self.side, self.price, self.quantity)


def create_db():
    Base.metadata.create_all(db_engine)
