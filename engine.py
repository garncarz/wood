from models import Order


def trade():
    bid = Order.query.filter_by(side='bid') \
            .order_by(Order.price.desc()).first()
    if bid is None:
        return False

    ask = Order.query.filter_by(side='ask') \
            .filter(Order.price <= bid.price) \
            .order_by(Order.price).first()
    if ask is None:
        return False

    return bid, ask
