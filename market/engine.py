from datetime import datetime

from .database import db_session
from .models import Order


def trade():
    buy = Order.query.filter_by(side='buy', active=True) \
            .order_by(Order.registered_at, Order.price.desc()) \
            .first()
    if buy is None:
        return False

    sell = Order.query.filter_by(side='sell', active=True) \
            .filter(Order.price <= buy.price) \
            .order_by(Order.registered_at, Order.price) \
            .first()
    if sell is None:
        return False

    price = buy.price
    quantity = min(buy.quantity, sell.quantity)

    buy.active = False
    sell.active = False
    buy.traded_to = sell
    sell.traded_to = buy
    db_session.add_all([buy, sell])

    if buy.quantity < sell.quantity:
        sell2 = Order(side='sell',
                      code=sell.code,
                      participant=sell.participant,
                      price=sell.price,
                      quantity=sell.quantity - buy.quantity,
                      registered_at=sell.registered_at)
        db_session.add(sell2)

    elif sell.quantity < buy.quantity:
        buy2 = Order(side='buy',
                     code=buy.code,
                     participant=buy.participant,
                     price=buy.price,
                     quantity=buy.quantity - sell.quantity,
                     registered_at=buy.registered_at)
        db_session.add(buy2)

    db_session.commit()

    return {
        'price': price,
        'quantity': quantity,
        'time': datetime.now(),
        'buy': buy,
        'sell': sell,
    }
