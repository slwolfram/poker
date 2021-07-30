from flask import json
import pytest
from .config import test_user
from poker import create_app
import os
import glob
import datetime
import dataset


@pytest.fixture(scope='session', autouse=True)
def client():
    app = create_app({'ENV': 'UNITTEST', 'DBCONN': 'sqlite:///temp.db'})
    assert 'DBCONN' in app.config
    yield app.test_client()
    for f in glob.glob('temp.db*'):
        os.remove(f)


def register_user(client, username, password, email):
    rv = client.post('api/user/register', json=dict(
        username=username,
        password=password,
        email=email
    ))
    return rv


@pytest.fixture
def registered_user(client):
    user_details = (test_user['USERNAME'], test_user['PASSWORD'],
                    test_user['EMAIL'])
    rv = register_user(client, *user_details)
    return rv.json


def login_user(client, username, email, password):
    rv = client.post('/api/user/login', json=dict(
        username=username,
        email=email,
        password=password
    ))
    return rv


@pytest.fixture
def logged_in_user1(client, registered_user):
    rv = login_user(
        client, registered_user['username'], None, registered_user['password'])
    return rv.json


def test_create_app(client):
    assert client is not None


def test_register_user(client):
    rv = register_user(client, test_user['USERNAME'], test_user['PASSWORD'],
                       test_user['EMAIL'])
    assert rv._status_code == 201
    assert 'ident' in rv.json


def test_login_user_with_username(client, registered_user):
    rv = login_user(client, registered_user['username'],
                    None, registered_user['password'])
    assert rv._status_code == 200
    assert 'auth_token' in rv.json
    assert rv.json['auth_token'] is not None


def test_login_user_with_email(client, registered_user):
    rv = login_user(
        client, None, registered_user['email'], registered_user['password'])
    assert rv._status_code == 200
    assert 'auth_token' in rv.json
    assert rv.json['auth_token'] is not None


def test_authentication(client, logged_in_user1):
    rv = client.get('api/user/testauth',
                    headers={'x-access-token': logged_in_user1['auth_token']})
    assert rv._status_code == 200


def test_authentication_fails_without_token(client):
    rv = client.get('api/user/testauth')
    assert rv._status_code == 401
    assert 'message' in rv.json
    assert rv.json['message'] == 'Missing auth token.'


def test_authentication_fails_with_invalid_token(client):
    rv = client.get('api/user/testauth',
                    headers={'x-access-token': 'badtoken'})
    assert rv._status_code == 401
    assert 'message' in rv.json
    assert rv.json['message'] == 'Invalid token.'


def test_authentication_fails_with_expired_token(client, logged_in_user1):
    dataset.connect('sqlite:///temp.db')['tokens'].update(
        {'auth_token': logged_in_user1['auth_token'],
         'token_expiry_dttm': datetime.datetime.now()}, ['auth_token'])
    rv = client.get('api/user/testauth',
                    headers={'x-access-token': logged_in_user1['auth_token']})
    assert rv._status_code == 401
    assert 'message' in rv.json
    assert rv.json['message'] == 'Token has expired.'


def create_2max_holdem_game(client, auth_token):
    rv = client.post('api/poker/',
                     json={'game_type': 'texas_holdem',
                           'num_seats': 2,
                           'big_blind': 50,
                           'small_blind': 25,
                           'min_buyin': 10000,
                           'max_buyin': 20000,
                           'table_name': 'TEST_TABLE'
                           },
                     headers={'x-access-token': auth_token})
    return rv


@pytest.fixture
def holdem_2max_game(client, logged_in_user1):
    rv = create_2max_holdem_game(client, logged_in_user1['auth_token'])
    return rv.json


def test_create_game(client, logged_in_user1):
    rv = create_2max_holdem_game(client, logged_in_user1['auth_token'])
    print(rv.json)
    assert rv._status_code == 201


def add_player(client, holdem_2max_game, logged_in_user1):
    rv = client.post('api/poker/player/',
                     json={'user_id': logged_in_user1['ident'],
                           'game_id': holdem_2max_game['ident'],
                           'seat_num': 1,
                           'buyin': 20000
                           },
                     headers={'x-access_token': logged_in_user1['auth_token']})
    return rv


def test_add_player(client, holdem_2max_game, logged_in_user1):
    rv = add_player(client, holdem_2max_game, logged_in_user1)
    assert rv._status_code == 200
