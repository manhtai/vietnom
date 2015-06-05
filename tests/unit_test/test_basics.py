from flask import current_app

def test_app_exists(session):
    assert not current_app is None

def test_app_is_testing(session):
    assert current_app.config['TESTING']
