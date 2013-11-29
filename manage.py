#!/usr/bin/env python
import os

import redis
from flask.ext.script import Server, Manager, Shell

from boby.main import create_app
from boby.lib.backends import get_backend
from boby.lib.utils import bootstrap_packages, import_config


# configuration from env var
config_file = os.environ['BOBY_SETTINGS']
config_file = os.path.realpath(os.path.expanduser(config_file)) 
print "config_file: ", config_file

# create the main Flask application
app = create_app(config_file=config_file, debug=True)

# Create and configure the Manager
manager = Manager(app)
manager.add_command("runserver", Server(host='0.0.0.0'))

@manager.shell
def make_shell_context():
    "(i)Python shell"
    return dict(app=app)

@manager.command
def dump_config():
    "Pretty print the config"
    for key in sorted(app.config.iterkeys()):
        print "%s: %s" % (key, app.config[key])

@manager.command
def cleanup_redis():
    import_config()
    r = RedisBackend().redis
    r.delete(*r.keys())

@manager.command
def cleanup_mongo(dbname):
    m = MongoBackend()
    m.mongo.drop_database(dbname)

@manager.command
def bootstrap_domain(domain):
    backend = get_backend()
    if not backend.domain_exists(domain):
        backend.create_domain(domain)
    backend.update_domain(domain, available_packages=bootstrap_packages().keys())

if __name__ == "__main__":
    manager.run()
