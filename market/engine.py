from .database import db_session
from .models import Order


def trade():
    buy = Order.query.filter_by(side='buy', traded=False) \
            .order_by(Order.registered_at, Order.price.desc()) \
            .first()
    if buy is None:
        return False

    sell = Order.query.filter_by(side='sell', traded=False) \
            .filter(Order.price <= buy.price) \
            .order_by(Order.registered_at, Order.price) \
            .first()
    if sell is None:
        return False

    price = buy.price
    quantity = min(buy.quantity, sell.quantity)

    buy.traded = True
    sell.traded = True
    db_session.add_all([buy, sell])

    if buy.quantity < sell.quantity:
        sell2 = Order(side='sell',
                      participant=sell.participant,
                      price=sell.price,
                      quantity=sell.quantity - buy.quantity,
                      registered_at=sell.registered_at)
        db_session.add(sell2)

    elif sell.quantity < buy.quantity:
        buy2 = Order(side='buy',
                     participant=buy.participant,
                     price=buy.price,
                     quantity=buy.quantity - sell.quantity,
                     registered_at=buy.registered_at)
        db_session.add(buy2)

    db_session.commit()

    return {
        'price': price,
        'quantity': quantity,
        'buy': buy,
        'sell': sell,
        'buyer': buy.participant,
        'seller': sell.participant,
    }
