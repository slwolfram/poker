from flask import Blueprint, request
from flask_restx import Api
from poker.api.user_api import api as user_api
from poker.api.poker_api import api as poker_api


bp = Blueprint("api", __name__)

authorizations = {
    'api_key': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'x-access-token'
    }
}

api = Api(bp,
          authorizations=authorizations,
          security='api_key',
          title='poker')

api.add_namespace(user_api)
api.add_namespace(poker_api)


