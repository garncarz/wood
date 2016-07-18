from datetime import datetime, timedelta
from functools import partial

from market.database import db_session
from market import engine
from market import factories

import test_models


def test_empty():
    """Test engine when there are no orders."""
    assert engine.trade() is False


def test_match():
    """Test basic matching."""

    test_models.test_table()
    factories.Order(side='sell', quantity=350, price=144)
    db_session.commit()

    trade1 = engine.trade()
    assert trade1['price'] == 145
    assert trade1['quantity'] == 100
    assert trade1['buy'].traded_to == trade1['sell']

    trade2 = engine.trade()
    assert trade2['price'] == 145
    assert trade2['quantity'] == 200

    trade3 = engine.trade()
    assert trade3['price'] == 144
    assert trade3['quantity'] == 50

    assert engine.trade() is False


def test_no_buys():
    """Test a case when there are no buying orders."""

    s = partial(factories.Order, side='sell')
    s(price=149, quantity=500)
    s(price=151, quantity=1000)
    s(price=151, quantity=300)
    db_session.commit()

    assert engine.trade() is False


def test_no_sells():
    """Test a case when there are no selling orders."""

    b = partial(factories.Order, side='buy')
    b(price=145, quantity=100)
    b(price=145, quantity=200)
    b(price=144, quantity=300)
    db_session.commit()

    assert engine.trade() is False


def test_correct_order():
    """Tests correct matching by both a creation time and a price."""

    now = datetime.now()

    s = partial(factories.Order, side='sell')
    sell1 = s(price=100, quantity=10, registered_at=now - timedelta(minutes=2))
    sell2 = s(price=90, quantity=5, registered_at=now - timedelta(minutes=1))
    sell3 = s(price=80, quantity=5, registered_at=now - timedelta(minutes=1))

    b = partial(factories.Order, side='buy')
    buy1 = b(price=110, quantity=5, registered_at=now - timedelta(minutes=2))
    buy2 = b(price=100, quantity=10, registered_at=now - timedelta(minutes=1))
    buy3 = b(price=120, quantity=10, registered_at=now - timedelta(minutes=1))

    db_session.commit()

    trade1 = engine.trade()
    assert trade1['sell'].code == sell3.code
    assert trade1['buy'].code == buy3.code
    assert trade1['price'] == 120
    assert trade1['quantity'] == 5

    trade2 = engine.trade()
    assert trade2['sell'].code == sell2.code
    assert trade2['buy'].code == buy3.code
    assert trade2['price'] == 120
    assert trade2['quantity'] == 5

    trade3 = engine.trade()
    assert trade3['sell'].code == sell1.code
    assert trade3['buy'].code == buy1.code
    assert trade3['price'] == 110
    assert trade3['quantity'] == 5

    trade4 = engine.trade()
    assert trade4['sell'].code == sell1.code
    assert trade4['buy'].code == buy2.code
    assert trade4['price'] == 100
    assert trade4['quantity'] == 5

    assert engine.trade() is False


def test_decimal():
    """Tests working with Decimals."""

    s = partial(factories.Order, side='sell')
    s(price=100.5, quantity=500)

    b = partial(factories.Order, side='buy')
    b(price=100.5, quantity=100)

    db_session.commit()

    trade = engine.trade()
    assert trade['price'] == 100.5
    assert trade['quantity'] == 100

    assert engine.trade() is False


def test_deactivated_participant():
    """Tests that orders from a deactivated participant are not tradeable."""

    participant = factories.Participant()

    s = partial(factories.Order, side='sell')
    s(price=100, quantity=500, participant=participant)

    b = partial(factories.Order, side='buy')
    b(price=100, quantity=100)

    db_session.commit()

    participant.deactivate()

    assert engine.trade() is False


def test_market_order_sell():
    """Tests matching MARKER sell orders."""

    test_models.test_table()
    factories.Order(side='market_sell', quantity=170, price=None)
    db_session.commit()

    trade1 = engine.trade()
    assert trade1['quantity'] == 100
    assert trade1['price'] == 145

    trade2 = engine.trade()
    assert trade2['quantity'] == 70
    assert trade2['price'] == 145

    assert engine.trade() is False


def test_market_order_buy():
    """Tests matching MARKER buy orders."""

    test_models.test_table()
    factories.Order(side='market_buy', quantity=602, price=None)
    db_session.commit()

    trade1 = engine.trade()
    assert trade1['quantity'] == 500
    assert trade1['price'] == 149

    trade2 = engine.trade()
    assert trade2['quantity'] == 102
    assert trade2['price'] == 151

    assert engine.trade() is False
