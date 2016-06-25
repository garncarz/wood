# StockMarketServer

This is an implementation of a simple one-stock market server,
as specified at [codingchallenge.wood.cz](http://codingchallenge.wood.cz/).

Implemented extra features:

- MARKET orders
- Decimal prices
- State saved in the database (but no logging in).
- Messages contain/support sequential ids.
- Orders belonging to a disconnected client are automatically deleted.

Logging to [Sentry](https://getsentry.com) is supported.


## Instalation

Needed: Python 3.5

1. `virtualenv3 virtualenv`
2. Make sure `virtualenv/bin` is in `PATH`.
3. `pip install -r requirements.txt`
4. Create `market/settings_local.py` if customized settings are needed.


## Use

Run `./server.py`, or `./server.py --help` if help is needed.


## Documentation

Run `make clean html` under the `doc` directory.
Generated documentation is located then under the `doc/_build/html` directory.


## Testing

Run `./test.sh`.