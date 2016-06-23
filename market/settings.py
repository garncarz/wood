import logging.config
import os

import raven


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

#: DB connection
DB_URL = 'sqlite:///:memory:'


SENTRY_DSN = None

LOGGING = lambda: {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'verbose': {
            'format': '[%(asctime)s][%(levelname)s] %(name)s '
                      '%(filename)s:%(funcName)s:%(lineno)d | %(message)s',
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'sentry': {
            'level': 'INFO',
            'class': 'raven.handlers.logging.SentryHandler',
            'dsn': SENTRY_DSN,
            'release': raven.fetch_git_sha(BASE_DIR),
        },
    },

    'loggers': {
        '': {
            'handlers': ['console', 'sentry'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

try:
    from .settings_local import *
except ImportError:
    pass

LOGGING = LOGGING()
logging.config.dictConfig(LOGGING)
