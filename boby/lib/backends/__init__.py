from ..utils import import_config

from .redisdb import RedisBackend
from .mongodb import MongoBackend


def get_backend(override=None):
    BACKEND = import_config().BACKEND if override is None else override
    if "mongodb" == BACKEND:
        return MongoBackend()
    elif "redis" == BACKEND:
        return RedisBackend()
