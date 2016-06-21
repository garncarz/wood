import asyncio
import json
import pytest

from market.server import ParticipantProtocol, DatastreamProtocol

# TODO check malicious/bad communication


async def send(writer, msg):
    writer.write(json.dumps(msg).encode('utf-8') + b'\n')
    await writer.drain()


async def read(reader):
    return json.loads((await reader.readline()).decode('utf-8'))


@pytest.mark.asyncio
async def test_process(event_loop, unused_tcp_port_factory):
    port = unused_tcp_port_factory()
    port_datastream = unused_tcp_port_factory()

    server = await event_loop.create_server(ParticipantProtocol,
                                            port=port)
    server_datastream = await event_loop.create_server(DatastreamProtocol,
                                                       port=port_datastream)

    reader1, writer1 = await asyncio.open_connection(port=port)
    reader2, writer2 = await asyncio.open_connection(port=port)
    datastream, _ = await asyncio.open_connection(port=port_datastream)

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'SELL',
        'price': 149,
        'quantity': 20,
    })
    answer = await read(reader1)
    assert answer['report'] == 'NEW'
    answer = await read(datastream)
    assert answer == {
        'type': 'orderbook',
        'side': 'ask',
        'price': 149,
        'quantity': 20,
    }

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 1234,
        'side': 'SELL',
        'price': 140,
        'quantity': 100,
    })
    answer = await read(reader1)
    assert answer['report'] == 'NEW'
    answer = await read(datastream)
    assert answer['price'] == 140

    await send(writer2, {
        'message': 'createOrder',
        'orderId': 987,
        'side': 'BUY',
        'price': 149,
        'quantity': 120,
    })
    answer = await read(reader2)
    assert answer['report'] == 'NEW'
    answer = await read(datastream)
    assert answer['side'] == 'bid'

    answer = await read(reader2)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 100
    answer = await read(reader1)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 100
    answer = await read(datastream)
    assert answer['type'] == 'trade'
    assert answer['price'] == 149
    assert answer['quantity'] == 100

    answer = await read(reader2)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 20
    answer = await read(reader1)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 20
    answer = await read(datastream)
    assert answer['type'] == 'trade'
    assert answer['price'] == 149
    assert answer['quantity'] == 20
