from flask import current_app, g
import dataset


def get_db():
    if 'db' not in g:
        print('connecting to db')
        g.db = dataset.connect(current_app.config['DBCONN'])
    return g.db
