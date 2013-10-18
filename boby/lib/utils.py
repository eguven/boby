import imp
import os

def import_config():
    config = os.environ.get('BOBY_SETTINGS', './config.rc')
    dd = imp.new_module('config')

    with open(config) as config_file:
        dd.__file__ = config_file.name
        exec(compile(config_file.read(), config_file.name, 'exec'), dd.__dict__)
    return dd

def bootstrap_packages():
    try:
        f = open(os.path.expanduser(import_config().BOBY_PROJECTS), "r")
        p = eval(f.read(), {"__builtins__":None}, {"True":True,"False":False})
        f.close()
        return p
    except Exception as e:
        print "Bootstrap brojects fail:", str(e)
        return {}

class CD(object):
    def __init__(self, directory=None):
        if directory is None:
            directory = os.getcwd()
        self.pwd = os.getcwd()
        self.target = os.path.expanduser(directory)

    def __enter__(self):
        os.chdir(self.target)

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.pwd)
