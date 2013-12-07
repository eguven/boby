import imp
import datetime
import os

from bson.objectid import ObjectId

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


def json_sanitizer(obj):
    """ObjectId and datetime sanitizer"""
    assert isinstance(obj, dict)
    converters = {ObjectId: str, datetime.datetime: lambda d: d.isoformat().split(".")[0]}
    def list_sanitizer(l):
        outlist = []
        for item in l:
            if type(item) in converters:
                outlist.append(converters[type(item)](item))
            else:
                outlist.append(item)
        return outlist
    def dict_sanitizer(d):
        outdict = {}
        for k, v in d.items():
            if type(v) in converters:
                outdict[k] = converters[type(v)](v)
            else:
                outdict[k] = v
        return outdict
    converters.update({list: list_sanitizer, dict: dict_sanitizer})
    return dict_sanitizer(obj)
