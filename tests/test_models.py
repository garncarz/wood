from functools import partial

from market.database import db_session
from market import models, factories


def test_table():
    """Tests filling a table with orders."""

    b = partial(factories.Order, side='buy')
    b(price=145, quantity=100)
    b(price=145, quantity=200)
    b(price=144, quantity=300)
    b(price=142, quantity=4500)

    s = partial(factories.Order, side='sell')
    s(price=149, quantity=500)
    s(price=151, quantity=1000)
    s(price=151, quantity=300)
    s(price=151, quantity=1200)
    s(price=156, quantity=150)

    db_session.commit()
