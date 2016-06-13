from database import db_session
from models import Order


def trade():
    bid = Order.query.filter_by(side='bid', traded=False) \
            .order_by(Order.registered_at, Order.price.desc()) \
            .first()
    if bid is None:
        return False

    ask = Order.query.filter_by(side='ask', traded=False) \
            .filter(Order.price <= bid.price) \
            .order_by(Order.registered_at, Order.price) \
            .first()
    if ask is None:
        return False

    price = bid.price
    quantity = min(bid.quantity, ask.quantity)

    bid.traded = True
    ask.traded = True
    db_session.add_all([bid, ask])

    if bid.quantity < ask.quantity:
        ask2 = Order(side='ask',
                     price=ask.price,
                     quantity=ask.quantity - bid.quantity,
                     registered_at=ask.registered_at)
        db_session.add(ask2)

    elif ask.quantity < bid.quantity:
        bid2 = Order(side='bid',
                     price=bid.price,
                     quantity=bid.quantity - ask.quantity,
                     registered_at=bid.registered_at)
        db_session.add(bid2)

    db_session.commit()

    return price, quantity
