from functools import partial

from database import db_session
import engine
import factories

import test_models


def test_empty():
    assert engine.trade() is False


def test_match():
    test_models.test_table()
    factories.Order(side='sell', quantity=350, price=144)
    db_session.commit()

    assert engine.trade() == (145, 100)
    assert engine.trade() == (145, 200)
    assert engine.trade() == (144, 50)
    assert engine.trade() is False


def test_no_buys():
    s = partial(factories.Order, side='sell')
    s(price=149, quantity=500)
    s(price=151, quantity=1000)
    s(price=151, quantity=300)
    db_session.commit()

    assert engine.trade() is False


def test_no_sells():
    b = partial(factories.Order, side='buy')
    b(price=145, quantity=100)
    b(price=145, quantity=200)
    b(price=144, quantity=300)
    db_session.commit()

    assert engine.trade() is False