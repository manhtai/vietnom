import pytest
from flask import url_for
from .conftest import TEST_EMAIL, TEST_PASSWORD, TEST_USERNAME

@pytest.mark.usefixtures('live_server')
def test_login_and_log_out(browser):
    browser.get(url_for('main.index', _external=True))

    browser.find_element_by_id('log-in').click()

    browser.wait_for_element_presence('log-in')

    browser.find_element_by_id('email').send_keys(TEST_EMAIL)
    browser.find_element_by_id('password').send_keys(TEST_PASSWORD)
    browser.find_element_by_id('submit').click()
    browser.wait_for_element_presence('log-out')

    browser.find_element_by_link_text(TEST_USERNAME).click()

    browser.find_element_by_id('settings').click()
    browser.find_element_by_id('change-password').click()

    browser.wait_for_element_presence('old_password')

    browser.find_element_by_id('old_password').send_keys(TEST_PASSWORD)
    browser.find_element_by_id('password').send_keys('Password1')
    browser.find_element_by_id('password2').send_keys('Password2')

    browser.find_element_by_id('submit').click()

    browser.find_element_by_id('old_password').send_keys(TEST_PASSWORD)
    browser.find_element_by_id('password').send_keys('Password1')
    browser.find_element_by_id('password2').send_keys('Password1')
    browser.find_element_by_id('submit').click()

    browser.wait_for_element_presence('log-out')
    browser.find_element_by_id('log-out').click()

    browser.wait_for_element_presence('log-in')

    browser.find_element_by_id('log-in').click()

    browser.find_element_by_id('email').send_keys(TEST_EMAIL)
    browser.find_element_by_id('password').send_keys(TEST_PASSWORD)
    browser.find_element_by_id('submit').click()

    browser.find_element_by_id('email').send_keys(TEST_EMAIL)
    browser.find_element_by_id('password').send_keys('Password1')
    browser.find_element_by_id('submit').click()


