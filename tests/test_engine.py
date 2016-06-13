from functools import partial

from database import db_session
import engine
import factories

import test_models


def test_empty():
    assert engine.trade() is False


def test_match():
    test_models.test_table()
    factories.Order(side='ask', quantity=350, price=144)
    db_session.commit()

    assert engine.trade() == (145, 100)
    assert engine.trade() == (145, 200)
    assert engine.trade() == (144, 50)
    assert engine.trade() is False


def test_no_bids():
    a = partial(factories.Order, side='ask')
    a(price=149, quantity=500)
    a(price=151, quantity=1000)
    a(price=151, quantity=300)
    db_session.commit()

    assert engine.trade() is False


def test_no_asks():
    b = partial(factories.Order, side='bid')
    b(price=145, quantity=100)
    b(price=145, quantity=200)
    b(price=144, quantity=300)
    db_session.commit()

    assert engine.trade() is False
