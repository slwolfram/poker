from flask import Flask
from flask_cors import CORS
from poker.api import bp


def create_app(config_dict):
    app = Flask(__name__)
    for k in config_dict.keys():
        app.config[k] = config_dict[k]
    print(app.config)
    CORS(app)
    print('creating app')
    app.register_blueprint(bp, url_prefix='/api')
    return app