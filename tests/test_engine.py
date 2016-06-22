from datetime import datetime, timedelta
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


def test_correct_order():
    now = datetime.now()

    s = partial(factories.Order, side='sell')
    sell1 = s(price=100, quantity=10, registered_at=now - timedelta(minutes=2))
    sell2 = s(price=90, quantity=5, registered_at=now - timedelta(minutes=1))

    b = partial(factories.Order, side='buy')
    buy1 = b(price=110, quantity=5, registered_at=now - timedelta(minutes=2))
    buy2 = b(price=100, quantity=10, registered_at=now - timedelta(minutes=1))

    db_session.commit()

    trade1 = engine.trade()
    assert trade1['sell'].id == sell1.id
    assert trade1['buy'].id == buy1.id
    assert trade1['price'] == 110
    assert trade1['quantity'] == 5

    trade2 = engine.trade()
    # assert trade2['sell'].id == sell1.id  # TODO parent_id?
    assert trade2['buy'].id == buy2.id
    assert trade2['price'] == 100
    assert trade2['quantity'] == 5

    trade3 = engine.trade()
    assert trade3['sell'].id == sell2.id
    # TODO assert trade3['buy'].id == buy2.id
    assert trade3['price'] == 100
    assert trade3['quantity'] == 5

    assert engine.trade() is False


def test_decimal():
    s = partial(factories.Order, side='sell')
    s(price=100.5, quantity=500)

    b = partial(factories.Order, side='buy')
    b(price=100.5, quantity=100)

    db_session.commit()

    trade = engine.trade()
    assert trade['price'] == 100.5
    assert trade['quantity'] == 100

    assert engine.trade() is False
