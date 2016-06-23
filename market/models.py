import logging

from sqlalchemy import (
    Column, Boolean, DateTime, Enum, Integer, Numeric,
    Table, ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base, db_engine, db_session

logger = logging.getLogger(__name__)


class Participant(Base):
    __tablename__ = 'participant'

    id = Column(Integer, primary_key=True)

    orders = relationship('Order', back_populates='participant',
                          cascade='all, delete-orphan')
    # TODO check deleting

    def __repr__(self):
        return '<Participant %d>' % self.id

    def deactivate(self):
        for order in self.orders:
            order.active = False
            db_session.add(order)
        db_session.commit()


class Order(Base):
    __tablename__ = 'order'

    id = Column(Integer, primary_key=True)
    code = Column(Integer, nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    traded_to_id = Column(Integer, ForeignKey(id), nullable=True)
    side = Column(Enum('buy', 'sell', 'market_buy', 'market_sell'),
                  nullable=False, index=True)
    price = Column(Numeric, nullable=True, index=True)
    participant_id = Column(Integer, ForeignKey(Participant.id), nullable=True)
    quantity = Column(Integer, nullable=False)
    registered_at = Column(DateTime, nullable=False, index=True,
                           default=func.now())

    participant = relationship('Participant', back_populates='orders')
    traded_to = relationship('Order', remote_side=[id], post_update=True)

    def __repr__(self):
        if self.side in ['buy', 'sell']:
            fmt = '<Order %(side)s/$%(price)d/%(quantity)d pcs>'
        else:
            fmt = '<Order %(side)s/%(quantity)d pcs>'
        return fmt % self.__dict__

    @property
    def side_datastream(self):
        if self.side == 'buy':
            return 'bid'
        if self.side == 'sell':
            return 'ask'


def create_db():
    logger.info('Creating DB schema...')
    Base.metadata.create_all(db_engine)
