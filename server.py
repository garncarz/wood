#!/usr/bin/env python3

import argparse
import logging

from market import models
from market.server import run


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


arg_parser = argparse.ArgumentParser(
    description='Simple stock market server',
)
arg_parser.add_argument('--create-db', action='store_true',
                        help='Creates DB schema.')
arg_parser.add_argument('--host', nargs='?', default='localhost',
                        help='Listen as, default is localhost.')
arg_parser.add_argument('--port', nargs='?', default=7001, type=int,
                        help='Listen on, default is 7001.')


if __name__ == '__main__':
    args = arg_parser.parse_args()

    if args.create_db:
        models.create_db()

    run(args.host, args.port)
