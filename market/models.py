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
    """Active participant, making bids/asks, trading."""

    __tablename__ = 'participant'

    id = Column(Integer, primary_key=True)
    """Primary key."""

    orders = relationship('Order', back_populates='participant',
                          cascade='all, delete-orphan')
    """Orders created by this participant."""
    # TODO check deleting

    def __repr__(self):
        return '<Participant %d>' % self.id

    def deactivate(self):
        """Deactivates this participant,
        effectively deactivating all his orders.
        """

        for order in self.orders:
            order.active = False
            db_session.add(order)
        db_session.commit()


class Order(Base):
    """Market's order."""

    __tablename__ = 'order'

    id = Column(Integer, primary_key=True)
    """Primary key."""

    code = Column(Integer, nullable=False, index=True)
    """Order's code as received in a message."""

    active = Column(Boolean, default=True, nullable=False, index=True)
    """Is the order tradeable? (Already traded or deleted are not.)"""

    traded_to_id = Column(Integer, ForeignKey(id), nullable=True)
    """Primary key of a linked traded order."""

    side = Column(Enum('buy', 'sell', 'market_buy', 'market_sell'),
                  nullable=False, index=True)
    """Order's role/side."""

    price = Column(Numeric, nullable=True, index=True)
    """Price, can be Decimal."""

    participant_id = Column(Integer, ForeignKey(Participant.id), nullable=True)
    """Primary key of a participant who created this order."""

    quantity = Column(Integer, nullable=False)
    """Quantity."""

    registered_at = Column(DateTime, nullable=False, index=True,
                           default=func.now())
    """DateTime of creation."""

    participant = relationship('Participant', back_populates='orders')
    """Participant (object) who created this order."""

    traded_to = relationship('Order', remote_side=[id], post_update=True)
    """Linked traded order (object)."""

    def __repr__(self):
        if self.side in ['buy', 'sell']:
            fmt = '<Order %(side)s/$%(price)d/%(quantity)d pcs>'
        else:
            fmt = '<Order %(side)s/%(quantity)d pcs>'
        return fmt % self.__dict__

    @property
    def side_datastream(self):
        """Helper translation (`buy` -> `bid`, `sell` -> `ask`)
        for working with messages.
        """

        if self.side == 'buy':
            return 'bid'
        if self.side == 'sell':
            return 'ask'


def create_db():
    """Creates the DB schema."""

    logger.info('Creating DB schema...')
    Base.metadata.create_all(db_engine)
