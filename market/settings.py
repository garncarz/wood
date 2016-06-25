import logging.config
import os

import raven

#: Base directory of the project.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

#: DB connection.
DB_URL = 'sqlite:///:memory:'

#: Sentry URL. If not `None`, logging to specified Sentry.
SENTRY_DSN = None

#: Logging dict configuration.
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
