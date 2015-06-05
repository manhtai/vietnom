import pytest
from app import create_app, db
from app.models import Role

@pytest.yield_fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    app = create_app('testing')

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()

@pytest.yield_fixture(scope='function')
def session(app):
    """Function-wide test database, 
    i.e, database is created and then dropped for each test"""

    db.app = app
    db.create_all()
    Role.insert_roles()

    yield db.session

    db.session.remove()
    db.drop_all()
