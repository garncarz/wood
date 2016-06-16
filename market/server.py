import asyncio
import json
import logging

from .database import db_session
from . import engine
from .models import Order
from . import models


logger = logging.getLogger(__name__)


class MarketException(Exception):
    pass


def process(message, participant):
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
                id=order_id,  # FIXME can't be id when it's cloned
                participant=participant,
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
        # FIXME don't delete, just mark
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


clients = {}


def _send(transport, msg):
    transport.write(json.dumps(msg).encode('utf-8') + b'\n')
    logger.debug('Message sent: %s' % msg)


class ServerProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info('peername')
        logger.debug('Connected: %s' % str(self.peername))

        self.participant = models.Participant()
        db_session.add(self.participant)
        db_session.commit()

        clients[self.participant.id] = self

    def data_received(self, data):
        message = json.loads(data.decode('utf-8'))
        logger.debug('Message received: %s' % message)

        try:
            reply = process(message, self.participant)
        except MarketException as e:
            logger.warning('Bad input: %s' % e)
            reply = {'error': str(e)}

        _send(self.transport, reply)

        trade = engine.trade()
        while trade:
            logger.info('Trade: %s' % trade)
            _send(clients[trade['buyer'].id].transport, {
                'message': 'executionReport',
                'orderId': trade['buy'].id,
                'report': 'FILL',
                'price': trade['price'],
                'quantity': trade['quantity'],
            })
            _send(clients[trade['seller'].id].transport, {
                'message': 'executionReport',
                'orderId': trade['sell'].id,
                'report': 'FILL',
                'price': trade['price'],
                'quantity': trade['quantity'],
            })
            trade = engine.trade()

    def connection_lost(self, exc):
        logger.debug('Disconnected: %s' % str(self.peername))
        del clients[self.participant.id]


def run(host, port):
    loop = asyncio.get_event_loop()
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
