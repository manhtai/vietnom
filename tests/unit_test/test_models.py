import pytest
import time
from datetime import datetime
from app.models import User, AnonymousUser, Permission

def test_password_setter(session):
    u = User(password='cat')
    assert u.password_hash is not None

def test_no_password_getter(session):
    u = User(password='cat')
    with pytest.raises(AttributeError):
        u.password

def test_password_verification(session):
    u = User(password='cat')
    assert u.verify_password('cat')
    assert not u.verify_password('dog')

def test_password_salts_are_random(session):
    u = User(password='cat')
    u2 = User(password='cat')
    assert u.password_hash != u2.password_hash

def test_valid_confirmation_token(session):
    u = User(password='cat')
    session.add(u)
    session.commit()
    token = u.generate_confirmation_token()
    assert u.confirm(token)

def test_invalid_confirmation_token(session):
    u1 = User(password='cat')
    u2 = User(password='dog')
    session.add(u1)
    session.add(u2)
    session.commit()
    token = u1.generate_confirmation_token()
    assert not u2.confirm(token)

def test_expired_confirmation_token(session):
    u = User(password='cat')
    session.add(u)
    session.commit()
    token = u.generate_confirmation_token(1)
    time.sleep(2)
    assert not u.confirm(token)

def test_valid_reset_token(session):
    u = User(password='cat')
    session.add(u)
    session.commit()
    token = u.generate_reset_token()
    assert u.reset_password(token, 'dog')
    assert u.verify_password('dog')

def test_invalid_reset_token(session):
    u1 = User(password='cat')
    u2 = User(password='dog')
    session.add(u1)
    session.add(u2)
    session.commit()
    token = u1.generate_reset_token()
    assert not u2.reset_password(token, 'horse')
    assert u2.verify_password('dog')

def test_valid_email_change_token(session):
    u = User(email='john@example.com', password='cat')
    session.add(u)
    session.commit()
    token = u.generate_email_change_token('susan@example.org')
    assert u.change_email(token)
    assert u.email == 'susan@example.org'

def test_invalid_email_change_token(session):
    u1 = User(email='john@example.com', password='cat')
    u2 = User(email='susan@example.org', password='dog')
    session.add(u1)
    session.add(u2)
    session.commit()
    token = u1.generate_email_change_token('david@example.net')
    assert not u2.change_email(token)
    assert u2.email == 'susan@example.org'

def test_duplicate_email_change_token(session):
    u1 = User(email='john@example.com', password='cat')
    u2 = User(email='susan@example.org', password='dog')
    session.add(u1)
    session.add(u2)
    session.commit()
    token = u2.generate_email_change_token('john@example.com')
    assert not u2.change_email(token)
    assert u2.email == 'susan@example.org'

def test_roles_and_permissions(session):
    u = User(email='john@example.com', password='cat')
    assert u.can(Permission.TELL)
    assert not u.can(Permission.CENSOR)

def test_anonymous_user(session):
    u = AnonymousUser()
    assert not u.can(Permission.VIEW)

def test_timestamps(session):
    u = User(password='cat')
    session.add(u)
    session.commit()
    assert (datetime.utcnow() - u.member_since).total_seconds() < 3
    assert (datetime.utcnow() - u.last_seen).total_seconds() < 3

def test_ping(session):
    u = User(password='cat')
    session.add(u)
    session.commit()
    time.sleep(2)
    last_seen_before = u.last_seen
    u.ping()
    assert u.last_seen > last_seen_before
