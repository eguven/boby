from flask import Flask
from flask.ext.restful import Api, representations

from .lib.resources import add_resources
from .lib.utils import json_sanitizer
from .web import bp as web_bp


class Api(Api):
    def __init__(self, *args, **kwargs):
        super(Api, self).__init__(*args, **kwargs)

        def json_wrapper(*args, **kwargs):
            data = json_sanitizer(args[0])
            return representations.json.output_json(data, *args[1:], **kwargs)

        self.representations["application/json"] = json_wrapper


def create_app(config_file=None, debug=False):
    """
    Factory for the main application.
    """
    app = Flask(__name__)

    import logging
    # configuration
    app.debug = debug

    if config_file:
        app.config.from_pyfile(config_file)

    # register blueprints
    app.register_blueprint(web_bp)
    api = add_resources(Api(app))

    return app

app = create_app()
