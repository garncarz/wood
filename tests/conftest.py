import pytest

from market import settings
settings.DB_URL = 'sqlite:///:memory:'

from market import models


@pytest.fixture(scope='session', autouse=True)
def db_prepare():
    """Creates the DB schema."""
    models.create_db()


@pytest.yield_fixture(scope='function', autouse=True)
def db_clean():
    """Removes all the orders after each test."""
    yield
    models.Order.query.delete()
