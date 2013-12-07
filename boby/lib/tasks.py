#!/usr/bin/env python
import os
import sys
import datetime
from redis import Redis

from .backends import get_backend
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
BACKEND = get_backend()
if not BACKEND.get_domain("main"):
    BACKEND.create_domain("main")
if not get_backend().get_domain("main")["available_packages"]:
    BACKEND.update_domain("main", available_packages=["test_config", "test_application"])

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
    sys.stdout = open(logfilepath, "a")
    sys.stderr = sys.stdout

    args = ["name", "url", "branch", "path_to_missile"]
    for arg in args:
        print arg, ":", locals()[arg]

    # with settings(host_string=host, key_filename=key_filename):
    wc = WorkingCopy(name, base_folder=os.path.expanduser("~/build"), repo=url)
    wc.prepare(branch=branch)

    latest_version = BACKEND.get_latest_version(name)
    new_base_version = wc.generate_new_base_version(latest_version)

    new_version = wc.get_new_git_version(prefix=new_base_version, suffix=branch)
    # skipping existing build removed
    wc.set_version(new_version)
    if path_to_missile:
        path_to_missile = os.path.join(wc.working_copy, path_to_missile)
    debs_path = os.path.expanduser(dd.BUILD_DEBSPATH)
    result = wc.build(path_to_missile=path_to_missile, output_path=debs_path, logpath=logfilepath)
    BACKEND.delete_lock("packages", name)
    for build_dict in result:
        print "BUILD DICT IS:", build_dict
        BACKEND.create_package(build_dict["name"], build_dict["version"], build_dict["file_name"])

        if domain is not None and stack is not None:
            BACKEND.add_stack_package(domain, stack, build_dict)
            print "Added to 'domains:%s:stacks:%s:packages' as {'%s': '%s'}" % (domain, stack, name, new_version)
