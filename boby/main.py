from flask import Flask
from flask.ext.restful import Api

from .lib.resources import add_resources
from .web import bp as web_bp


def create_app(config_file=None, debug=False):
    """
    Factory for the main application.
    """
    app = Flask(__name__)

    # configuration
    app.debug = debug
    if config_file:
        app.config.from_pyfile(config_file)

    # register blueprints
    app.register_blueprint(web_bp)
    api = add_resources(Api(app))

    return app
