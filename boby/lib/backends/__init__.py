from ..utils import import_config

from .redisdb import RedisBackend
from .mongodb import MongoBackend

def get_backend():
    BACKEND = import_config().BACKEND
    if "mongodb" == BACKEND:
        return MongoBackend()
    elif "redis" == BACKEND:
        return RedisBackend()