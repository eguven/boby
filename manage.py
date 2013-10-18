#!/usr/bin/env python
import os

import redis
from flask.ext.script import Server, Manager, Shell

from boby.main import create_app
from boby.lib.backends import RedisBackend
from boby.lib.utils import bootstrap_packages


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
    from boby.lib.utils import import_config
    import_config()
    r = RedisBackend().redis
    r.delete(*r.keys())

@manager.command
def bootstrap_domain(domain):
    if not RedisBackend().domain_exists(domain):
        RedisBackend().create_domain(domain)
    RedisBackend().update_domain(domain, available_packages=bootstrap_packages().keys())

if __name__ == "__main__":
    manager.run()
