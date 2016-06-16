import random

from factory import lazy_attribute
from factory.alchemy import SQLAlchemyModelFactory

from .database import db_session
from . import models


lazy = lambda call: lazy_attribute(lambda obj: call())
lazy_bool = lazy(lambda: random.choice([True, False]))
lazy_choice = lambda choices: lazy(lambda: random.choice(choices))
lazy_randint = lambda min, max: lazy(lambda: random.randint(min, max))


class Order(SQLAlchemyModelFactory):
    class Meta:
        model = models.Order
        sqlalchemy_session = db_session

    side = lazy_choice(['ask', 'bid'])
    price = lazy_randint(1, 1000)
    quantity = lazy_randint(1, 1000)
