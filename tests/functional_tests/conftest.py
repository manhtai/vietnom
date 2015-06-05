import pytest
from app import create_app, db
from app.models import Role, User
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# Uncomment for using Xvfb in CI server
# from pyvirtualdisplay import Display

TEST_EMAIL = 'jonh@example.com'
TEST_PASSWORD  = 'this_is_very_secret'
TEST_USERNAME = 'john'

@pytest.yield_fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    app = create_app('testing')

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()

@pytest.yield_fixture(scope='session')
def session(app):
    """Session-wide test database, 
    i.e, database is created and then dropped for each test"""

    db.drop_all()

    db.app = app
    db.create_all()
    Role.insert_roles()

    # Create user example
    u = User(email=TEST_EMAIL, password=TEST_PASSWORD, username=TEST_USERNAME,\
             confirmed=True)
    db.session.add(u)
    db.session.commit()

    yield db.session

    db.session.remove()
    db.drop_all()

@pytest.yield_fixture(scope='function')
def browser(session):
    """Function-wide selenium test"""

    # display = Display(visible=0, size=(1024, 768))
    # display.start()
    browser = webdriver.Firefox()

    def wait_for_element_presence(ELEMENT_NAME, BY=By.ID):
        WebDriverWait(browser, timeout=30).until(
            EC.presence_of_element_located((BY, ELEMENT_NAME))
        )

    browser.wait_for_element_presence = wait_for_element_presence

    yield browser

    browser.quit()
    # display.stop()
