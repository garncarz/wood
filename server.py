#!/usr/bin/env python3

import asyncio
import functools
import json
import logging

logger = logging.getLogger('server')
logging.basicConfig(level=logging.DEBUG)


class MarketException(Exception):
    pass


class MarketModel:

    def __init__(self):
        self.orders = {}

    def apply(self, message):
        try:
            action = message['message']
            order_id = int(message['orderId'])
        except KeyError:
            raise MarketException('Unsufficient data.')

        if action == 'createOrder':
            if order_id in self.orders:
                raise MarketException('Order already exists.')
            try:
                self.orders[order_id] = {
                    'side': message['side'],
                    'price': message['price'],
                    'quantity': message['quantity'],
                }
            except KeyError:
                raise MarketException('Unsufficient data.')
            logger.debug('Order created: %s' % self.orders[order_id])
            report = 'NEW'

        elif action == 'cancelOrder':
            if not order_id in self.orders:
                raise MarketException('Order does not exist.')
            self.orders.pop(order_id)
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

    def __str__(self):
        return str(self.orders)


class ServerProtocol(asyncio.Protocol):

    def __init__(self, model):
        self.model = model

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        message = json.loads(data.decode('utf-8'))
        logger.debug('Message received: %s' % message)

        try:
            reply = self.model.apply(message)
        except MarketException as e:
            logger.warning('Bad input: %s' % e)
            reply = {'error': str(e)}

        self.transport.write((json.dumps(reply) + '\n').encode('utf-8'))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    host = 'localhost'
    port = 7001
    coro = loop.create_server(functools.partial(ServerProtocol, MarketModel()),
                              host, port)
    server = loop.run_until_complete(coro)

    logger.info('Listening on %s:%s' % (host, port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
