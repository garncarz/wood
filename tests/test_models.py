from functools import partial

from database import db_session
import models, factories


def test_table():
    b = partial(factories.Order, side='bid')
    b(price=145, quantity=100)
    b(price=145, quantity=200)
    b(price=144, quantity=300)
    b(price=142, quantity=4500)

    a = partial(factories.Order, side='ask')
    a(price=149, quantity=500)
    a(price=151, quantity=1000)
    a(price=151, quantity=300)
    a(price=151, quantity=1200)
    a(price=156, quantity=150)

    db_session.commit()
