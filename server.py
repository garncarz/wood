#!/usr/bin/env python3

import asyncio
import json
import logging

logger = logging.getLogger('server')
logging.basicConfig(level=logging.DEBUG)


class Server(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        command = json.loads(data.decode('utf-8'))
        logger.debug('Command received: %s' % command)

        action = command['message']
        order_id = command['orderId']

        if action == 'createOrder':
            report = 'NEW'
        elif action == 'cancelOrder':
            report = 'CANCELED'
        else:
            logger.warning('Unknown action: %s' % action)
            report = 'UNKNOWN_MESSAGE'

        reply = {
            'message': 'executionReport',
            'orderId': order_id,
            'report': report,
        }
        self.transport.write((json.dumps(reply) + '\n').encode('utf-8'))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    host = 'localhost'
    port = 7001
    coro = loop.create_server(Server, host, port)
    server = loop.run_until_complete(coro)

    logger.info('Listening on %s:%s' % (host, port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
