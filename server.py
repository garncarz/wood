#!/usr/bin/env python3

import asyncio
import functools
import json
import logging

from database import db_session
from models import Order
import models


logger = logging.getLogger('server')
logging.basicConfig(level=logging.DEBUG)


class MarketException(Exception):
    pass


def process(message):
    try:
        action = message['message']
        order_id = int(message['orderId'])
    except KeyError:
        raise MarketException('Unsufficient data.')

    if action == 'createOrder':
        if Order.query.filter_by(id=order_id).count():
            raise MarketException('Order already exists.')
        try:
            order = Order(
                id=order_id,
                side=message['side'].lower(),
                price=message['price'],
                quantity=message['quantity'],
            )
            db_session.add(order)
            db_session.commit()
        except KeyError:
            raise MarketException('Unsufficient data.')
        logger.debug('Order created: %s' % order)
        report = 'NEW'

    elif action == 'cancelOrder':
        if not Order.query.filter_by(id=order_id).count():
            raise MarketException('Order does not exist.')
        Order.query.filter_by(id=order_id).delete()
        logger.debug('Order canceled: id=%d' % order_id)
        report = 'CANCELED'

    else:
        logger.warning('Unknown action: %s' % action)
        raise MarketException('Unknown action.')

    return {
        'message': 'executionReport',
        'orderId': order_id,
        'report': report,
    }


class ServerProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        message = json.loads(data.decode('utf-8'))
        logger.debug('Message received: %s' % message)

        try:
            reply = process(message)
        except MarketException as e:
            logger.warning('Bad input: %s' % e)
            reply = {'error': str(e)}

        self.transport.write((json.dumps(reply) + '\n').encode('utf-8'))


if __name__ == '__main__':
    models.create_db()  # TODO make persistent

    loop = asyncio.get_event_loop()
    host = 'localhost'
    port = 7001
    coro = loop.create_server(ServerProtocol, host, port)
    server = loop.run_until_complete(coro)

    logger.info('Listening on %s:%s' % (host, port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
