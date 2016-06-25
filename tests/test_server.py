import asyncio
import json
import pytest

from market.server import ParticipantProtocol, DatastreamProtocol


async def send(writer, msg):
    writer.write(json.dumps(msg).encode('utf-8') + b'\n')
    await writer.drain()


async def read(reader):
    return json.loads((await reader.readline()).decode('utf-8'))


@pytest.mark.asyncio
async def test_process(event_loop, unused_tcp_port_factory):
    """Complex test."""

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
        'seqId': 1,
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


@pytest.mark.asyncio
async def test_cancel(event_loop, unused_tcp_port):
    port = unused_tcp_port

    server = await event_loop.create_server(ParticipantProtocol,
                                            port=port)
    reader1, writer1 = await asyncio.open_connection(port=port)
    reader2, writer2 = await asyncio.open_connection(port=port)

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'SELL',
        'price': 149,
        'quantity': 20,
    })
    answer = await read(reader1)
    assert answer['report'] == 'NEW'

    await send(writer1, {
        'message': 'cancelOrder',
        'orderId': 123,
    })
    answer = await read(reader1)
    assert answer['report'] == 'CANCELED'

    await send(writer2, {
        'message': 'createOrder',
        'orderId': 987,
        'side': 'BUY',
        'price': 149,
        'quantity': 120,
    })
    answer = await read(reader2)
    assert answer['report'] == 'NEW'

    # TODO check there's no trade made


@pytest.mark.asyncio
async def test_cancel_bad_id(event_loop, unused_tcp_port):
    port = unused_tcp_port

    server = await event_loop.create_server(ParticipantProtocol,
                                            port=port)
    reader1, writer1 = await asyncio.open_connection(port=port)

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'SELL',
        'price': 149,
        'quantity': 20,
    })
    answer = await read(reader1)
    assert answer['report'] == 'NEW'

    await send(writer1, {
        'message': 'cancelOrder',
        'orderId': 1234,
    })
    answer = await read(reader1)
    assert 'error' in answer


@pytest.mark.asyncio
async def test_cancel_foreign_id(event_loop, unused_tcp_port):
    port = unused_tcp_port

    server = await event_loop.create_server(ParticipantProtocol,
                                            port=port)
    reader1, writer1 = await asyncio.open_connection(port=port)
    reader2, writer2 = await asyncio.open_connection(port=port)

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'SELL',
        'price': 149,
        'quantity': 20,
    })
    answer = await read(reader1)
    assert answer['report'] == 'NEW'

    await send(writer2, {
        'message': 'cancelOrder',
        'orderId': 123,
    })
    answer = await read(reader2)
    assert 'error' in answer


@pytest.mark.asyncio
async def test_cancel_partly_traded(event_loop, unused_tcp_port):
    port = unused_tcp_port
    server = await event_loop.create_server(ParticipantProtocol,
                                            port=port)
    reader1, writer1 = await asyncio.open_connection(port=port)
    reader2, writer2 = await asyncio.open_connection(port=port)

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'SELL',
        'price': 149,
        'quantity': 20,
    })
    answer = await read(reader1)
    assert answer['report'] == 'NEW'

    await send(writer2, {
        'message': 'createOrder',
        'orderId': 987,
        'side': 'BUY',
        'price': 149,
        'quantity': 120,
    })
    answer = await read(reader2)
    assert answer['report'] == 'NEW'

    answer = await read(reader2)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 20
    answer = await read(reader1)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 20

    await send(writer2, {
        'message': 'cancelOrder',
        'orderId': 987,
    })
    answer = await read(reader2)
    assert answer['report'] == 'CANCELED'

    # TODO try to make some trade


@pytest.mark.asyncio
async def test_bad_seq_id(event_loop, unused_tcp_port):
    port = unused_tcp_port
    server = await event_loop.create_server(ParticipantProtocol,
                                            port=port)
    reader1, writer1 = await asyncio.open_connection(port=port)

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'SELL',
        'price': 149,
        'quantity': 20,
        'seqId': 2,
    })
    answer = await read(reader1)
    assert answer['error'] == 'Bad seq id, expected 1'


@pytest.mark.asyncio
async def test_market_buy(event_loop, unused_tcp_port):
    port = unused_tcp_port
    server = await event_loop.create_server(ParticipantProtocol,
                                            port=port)
    reader1, writer1 = await asyncio.open_connection(port=port)
    reader2, writer2 = await asyncio.open_connection(port=port)

    await send(writer1, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'SELL',
        'price': 149,
        'quantity': 20,
    })
    answer = await read(reader1)
    assert answer['report'] == 'NEW'

    await send(writer2, {
        'message': 'createOrder',
        'orderId': 987,
        'side': 'MARKET_BUY',
        'quantity': 120,
    })
    answer = await read(reader2)
    assert answer['report'] == 'NEW'

    answer = await read(reader2)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 20
    answer = await read(reader1)
    assert answer['report'] == 'FILL'
    assert answer['price'] == 149
    assert answer['quantity'] == 20
