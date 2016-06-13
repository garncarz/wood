import asyncio
import json
import pytest

from server import ServerProtocol


async def send(writer, msg):
    writer.write(json.dumps(msg).encode('utf-8') + b'\n')
    await writer.drain()


async def read(reader):
    return json.loads((await reader.readline()).decode('utf-8'))


@pytest.mark.asyncio
async def test_process(event_loop, unused_tcp_port):
    server = await event_loop.create_server(ServerProtocol,
                                            port=unused_tcp_port)
    reader, writer = await asyncio.open_connection(port=unused_tcp_port)

    await send(writer, {
        'message': 'createOrder',
        'orderId': 123,
        'side': 'BUY',
        'price': 1000,
        'quantity': 4,
    })
    answer = await read(reader)
    assert answer['report'] == 'NEW'
