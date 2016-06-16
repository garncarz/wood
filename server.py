#!/usr/bin/env python3

import logging

from market import models
from market.server import run


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    models.create_db()  # TODO make persistent

    host = 'localhost'
    port = 7001
    run(host, port)
