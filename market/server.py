import asyncio
import simplejson as json
import logging

from .database import db_session
from . import engine
from .models import Order
from . import models


logger = logging.getLogger(__name__)


class MarketException(Exception):
    pass


def process(message, participant):
    order = None

    try:
        action = message['message']
        order_code = message['orderId']
    except KeyError:
        raise MarketException('Unsufficient data.')

    if action == 'createOrder':
        if Order.query.filter_by(code=order_code).count():
            raise MarketException('Order already exists.')
        try:
            order = Order(
                code=order_code,
                participant=participant,
                side=message['side'].lower(),
                quantity=message['quantity'],
            )
            if order.side in ['buy', 'sell']:
                order.price = message['price']
            db_session.add(order)
            db_session.commit()
        except KeyError:
            raise MarketException('Unsufficient data.')
        logger.info('Order created: %s' % order)
        report = 'NEW'

    elif action == 'cancelOrder':
        order_query = Order.query.filter_by(code=order_code,
                                            active=True,
                                            participant=participant)
        if not order_query.count():
            raise MarketException('Order does not exist.')
        order_query.update({Order.active: False})
        db_session.commit()
        logger.debug('Order canceled: id=%d' % order_code)
        report = 'CANCELED'

    else:
        logger.warning('Unknown action: %s' % action)
        raise MarketException('Unknown action.')

    return order, {
        'message': 'executionReport',
        'orderId': order_code,
        'report': report,
    }


#: Active clients (mapping models.Participant.id -> ParticipantProtocol).
participants = {}

#: Watching clients (list of DatastreamProtocol instances).
watchers = []


def _send(client, msg):
    """Sends a message to the client.

    :param asyncio.Protocol client: Client containing `.transport`.
    :param dict msg: Message to be JSONified.
    """

    client.outcoming_seq_id += 1
    msg['seqId'] = client.outcoming_seq_id

    client.transport.write(json.dumps(msg).encode('utf-8') + b'\n')
    logger.debug('Message sent: %s' % msg)


def _send_datastream_orderbook(order):
    """Informs watchers about a new order (anonymously).

    :param models.Order order: A new order.
    """

    msg = {
        'type': 'orderbook',
        'side': order.side_datastream,
        'price': order.price,
        'quantity': order.quantity,
    }

    for watcher in watchers:
        _send(watcher, msg)


def _send_datastream_trade(trade):
    """Informs watchers about a new trade (anonymously).

    :param dict trade: Trade (as returned from the engine).
    """

    msg = {
        'type': 'trade',
        'time': trade['time'].timestamp(),
        'price': trade['price'],
        'quantity': trade['quantity'],
    }

    for watcher in watchers:
        _send(watcher, msg)


def _make_trades():
    """As long as new trades can be make, make them
    and inform both participants and watchers.
    """

    trade = engine.trade()
    while trade:
        logger.info('Trade: %s' % trade)

        for side in ['buy', 'sell']:
            pid = trade[side].participant.id
            if not pid in participants:
                logger.warning('%s is already disconnected'
                               % trade[side].participant)
                continue

            _send(participants[pid],
                  {
                    'message': 'executionReport',
                    'orderId': trade[side].id,
                    'report': 'FILL',
                    'price': trade['price'],
                    'quantity': trade['quantity'],
                  },
            )

        _send_datastream_trade(trade)

        trade = engine.trade()


class ParticipantProtocol(asyncio.Protocol):
    """Protocol for active clients, those making bids/asks.
    """

    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info('peername')
        logger.debug('Connected: %s' % str(self.peername))

        self.participant = models.Participant()
        db_session.add(self.participant)
        db_session.commit()

        participants[self.participant.id] = self

        self.incoming_seq_id = 0
        self.outcoming_seq_id = 0

    def data_received(self, data):
        message = json.loads(data.decode('utf-8'))
        logger.debug('Message received: %s' % message)
        self.incoming_seq_id += 1

        order = None

        try:
            if 'seqId' in message:
                if not message['seqId'] == self.incoming_seq_id:
                    raise MarketException('Bad seq id, expected %d'
                                          % self.incoming_seq_id)
            order, reply = process(message, self.participant)
        except MarketException as e:
            logger.warning('Bad input: %s' % e)
            reply = {'error': str(e)}

        _send(self, reply)
        if order:
            _send_datastream_orderbook(order)

        _make_trades()

    def connection_lost(self, exc):
        logger.debug('Disconnected: %s' % str(self.peername))
        self.participant.deactivate()
        del participants[self.participant.id]


class DatastreamProtocol(asyncio.Protocol):
    """Protocol for anonymous watchers.

    .. todo::
        What about cancelling orders? Should watchers be informed?
        What's the format?
    """

    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info('peername')
        logger.debug('Connected (watcher): %s' % str(self.peername))

        watchers.append(self)

        self.outcoming_seq_id = 0

    def connection_lost(self, exc):
        logger.debug('Disconnected (watcher): %s' % str(self.peername))
        watchers.remove(self)


def run(host, port, port_datastream):
    """Runs both active & watcher services. Runs until Ctrl+C.

    :param str host: Listen as (e.g. `localhost`).
    :param int port: Listening port for active clients.
    :param int port_datatream: Listening port for watchers.
    """

    loop = asyncio.get_event_loop()

    coro = loop.create_server(ParticipantProtocol, host, port)
    server = loop.run_until_complete(coro)

    coro_datastream = loop.create_server(DatastreamProtocol, host,
                                         port_datastream)
    server_datastream = loop.run_until_complete(coro_datastream)

    logger.info('Listening on %s:%s,%s' % (host, port, port_datastream))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    server_datastream.close()
    loop.run_until_complete(server.wait_closed())
    loop.run_until_complete(server_datastream.wait_closed())
    loop.close()
