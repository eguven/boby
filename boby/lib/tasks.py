#!/usr/bin/env python
import os
import sys
import datetime
from redis import Redis

from .backends import RedisBackend
from .working_copy import WorkingCopy
from .utils import import_config

import pprint
pp = pprint.PrettyPrinter(indent=2)

# load config from file via environ variable
dd = import_config()

# get settings
key_filename = None if not hasattr(dd, "BUILD_KEY_FILENAME") else dd.BUILD_KEY_FILENAME
host = dd.BUILD_HOST

# TODO REMOVE - FOR EASY TESTING
if not RedisBackend().get_domain("main"):
    RedisBackend().create_domain("main")
if not RedisBackend().get_domain("main")["available_packages"]:
    RedisBackend().update_domain("main", available_packages=["test_config", "test_application"])

def send_notification(data):
    """
    Send notification using Pubsub Redis
    """
    red = Redis(dd.REDIS_HOST, int(dd.REDIS_PORT))
    red.publish("all", ['publish', data])

def package_build_process(name, url, branch, path_to_missile=None,
                          domain=None, stack=None):
    """
    Prepare working copy, checkout working copy, build
    """
    logfilename = "build-%s-%s-%s.log" % (name, branch, datetime.datetime.utcnow().isoformat())
    logfilepath = os.path.expanduser(os.path.join(dd.BUILD_LOGPATH, logfilename))
    sys.stdout = open(logfilepath, "w")
    sys.stderr = sys.stdout

    args = ["name", "url", "branch", "path_to_missile"]
    for arg in args:
        print arg , ": ", locals()[arg]

    # with settings(host_string=host, key_filename=key_filename):
    wc = WorkingCopy(name, base_folder=os.path.expanduser("~/build"), repo=url)
    wc.prepare(branch=branch)

    latest_version = RedisBackend().get_latest_version(name)
    new_base_version = wc.generate_new_base_version(latest_version)

    new_version = wc.get_new_git_version(prefix=new_base_version, suffix=branch)
    # skipping existing build removed
    wc.set_version(new_version)
    if path_to_missile:
        path_to_missile = os.path.join(wc.working_copy, path_to_missile)
    debs_path = os.path.expanduser(dd.BUILD_DEBSPATH)
    result = wc.build(path_to_missile=path_to_missile, output_path=debs_path)
    RedisBackend().delete_lock("packages", name)
    RedisBackend().create_package(name, new_version, result)
    print "Built new:", name, branch, new_version

    if domain is not None and stack is not None:
        RedisBackend().add_stack_package(domain, stack, name, new_version)
        print "Added to 'domains:%s:stacks:%s:packages' as {'%s': '%s'}" % (domain, stack, name, new_version)
