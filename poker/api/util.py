from functools import wraps
from flask import request
from poker.db import get_db
import datetime


def token_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
            tk_table = get_db()['tokens']
            res = tk_table.find_one(auth_token=token)
            if not res:
                return {'message': 'Invalid token.'}, 401
            if res['token_expiry_dttm'] <= datetime.datetime.now():
                tk_table.delete(auth_token=token)
                return {'message': 'Token has expired.'}, 401
            else:
                res['token_expiry_dttm'] = res['token_expiry_dttm'] + datetime.timedelta(hours=1)
                tk_table.update(res, ['auth_token'])
        else:
            return {'message': 'Missing auth token.'}, 401
        return f(*args, **kwargs)
    return inner