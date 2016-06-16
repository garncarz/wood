from functools import partial

from market.database import db_session
from market import engine
from market import factories

import test_models


def test_empty():
    assert engine.trade() is False


def test_match():
    test_models.test_table()
    factories.Order(side='sell', quantity=350, price=144)
    db_session.commit()

    trade1 = engine.trade()
    assert trade1['price'] == 145
    assert trade1['quantity'] == 100

    trade2 = engine.trade()
    assert trade2['price'] == 145
    assert trade2['quantity'] == 200

    trade3 = engine.trade()
    assert trade3['price'] == 144
    assert trade3['quantity'] == 50

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
