from database import db_session
import engine
import factories

import test_models


def test_match():
    test_models.test_table()
    factories.Order(side='ask', quantity=350, price=144)
    db_session.commit()

    assert engine.trade() == (145, 100)
    assert engine.trade() == (145, 200)
    assert engine.trade() == (144, 50)
