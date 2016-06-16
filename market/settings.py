import logging

#: DB connection
DB_URL = 'sqlite:///:memory:'

logging.basicConfig(level=logging.DEBUG)


try:
    from .settings_local import *
except ImportError:
    pass
