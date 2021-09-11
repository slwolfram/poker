from flask_restx import Namespace, Resource
import uuid
import datetime
from poker.db import get_db
from poker.api.util import token_required

api = Namespace('user')

user_parser = api.parser()
user_parser.add_argument('username', type=str, location='json')
user_parser.add_argument('email', type=str, location='json')
user_parser.add_argument('password', type=str, location='json')


def get_user(username, email, password):
    user = None
    users = get_db()['users']
    if username:
        user = users.find_one(username=username, password=password)
    elif email:
        user = users.find_one(email=email, password=password)
    return user if user else None


def update_user(user):

    users = get_db()['users']
    users.update(user, ['user_id'])


def insert_user(user):
    get_db()['users'].insert(user)


def set_auth_token(user):
    user['auth_token'] = str(uuid.uuid4())
    token = {'user_id': user['user_id'],
             'auth_token': user['auth_token'],
             'token_expiry_dttm': datetime.datetime.now() + datetime.timedelta(hours=1)
             }
    get_db()['tokens'].insert(token)


@api.route('/register')
class RegisterUser(Resource):
    @api.expect(user_parser)
    def post(self):
        user = user_parser.parse_args()
        user['user_id'] = str(uuid.uuid4())
        user['role'] = 'USER'
        set_auth_token(user)
        insert_user(user)
        return user, 201


@api.route('/login')
class LoginUser(Resource):
    @api.expect(user_parser)
    def post(self):
        userdata = user_parser.parse_args()
        user = get_user(userdata['username'],
                        userdata['email'], userdata['password'])
        if not user:
            return 'User does not exist', 400
        else:
            set_auth_token(user)
            update_user(user)
        return user, 200


@api.route('/testauth')
class TestAuth(Resource):
    @api.doc(security='api_key')
    @token_required
    def get(self, user_id):
        return 'Success', 200
