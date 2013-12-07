import json

import flask
from flask import Flask, request
from flask.ext.restful import Resource, abort, reqparse

from .tasks import package_build_process
from .backends import get_backend
from .utils import bootstrap_packages, import_config

PROJECTS_DATA = {
    'test_config': {
        'repo': 'git@github.com:ops-hero/test_config.git',
        'missile': None
    },
    'test_application': {
        'repo': 'git@github.com:ops-hero/test_application.git',
        'missile': None
    },
}

PROJECTS_DATA.update(bootstrap_packages())

import pprint
pp = pprint.PrettyPrinter(indent=2)
pp.pprint(PROJECTS_DATA)

class BaseResource(Resource):
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.reqparse = reqparse.RequestParser()
        self.backend = get_backend()


class DomainList(BaseResource):
    def get(self):
        return {"domains": map(lambda domain: domain["_id"], self.backend.list_domains())}

class Domain(BaseResource):
    def get(self, domain):
        domain = self.backend.get_domain(domain)
        return domain if domain else abort(404)

    def put(self, domain):  # TODO maybe POST?
        try:
            self.backend.create_domain(domain)
            return {"status": 201, "message": "Created"}
        except TypeError as e:
            abort(409, status=409, message="Conflict", info=str(e))

class StackList(BaseResource):
    def get(self, domain):
        self.reqparse.add_argument("detail", type=str)
        args = self.reqparse.parse_args()
        if args["detail"]:
            stacks = self.backend.list_stacks(domain, detail=True)
        else:
            stacks = self.backend.list_stacks(domain)
        return {"stacks": stacks}

class Stack(BaseResource):
    def get(self, domain, stack):
        print "Getting: %s:%s" % (domain, stack)
        stack = self.backend.get_stack(domain, stack)
        return stack if stack else abort(404, status=404, info="Stack not found")

    def put(self, domain, stack):
        self.reqparse.add_argument("copy_packages_from", type=str)
        args = self.reqparse.parse_args()
        source = args["copy_packages_from"]
        try:
            self.backend.create_stack(domain, stack)
        except TypeError as e:
            print e
            abort(409, status=409, message="Conflict", info=str(e))
        if source:
            try:
                self.backend.copy_stack_packages(domain=domain, source=source, dest=stack)
            except AssertionError as e:
                print e
                abort(400, status=400, message=repr(e))
        return {"status": 201, "message": "Created"}

class Build(BaseResource):
    def put(self, project):
        self.reqparse.add_argument("branch", type=str, default="master")
        self.reqparse.add_argument("domain", type=str)
        self.reqparse.add_argument("stack", type=str)
        args = self.reqparse.parse_args()
        branch, domain, stack = args["branch"], args["domain"], args["stack"]
        
        if domain and stack:
            if not self.backend.stack_exists(domain, stack):
                abort(404, status=404, message="Not Found", info="Domain and/or stack does not exist")
        if project not in PROJECTS_DATA:
            abort(404, status=404, message="Not Found", info="Project not found")
        try:
            self.backend.create_lock("packages", project)
        except TypeError as e:
            print e
            abort(409, status=409, message="Conflict", info="Build in progress")
        from multiprocessing import Process
        p = Process(target=package_build_process,
                    args=(project, PROJECTS_DATA[project]["repo"], branch),
                    kwargs={"path_to_missile": PROJECTS_DATA[project].get("missile", ".missile.yml"),
                            "domain": domain, "stack":stack},
                   )
        p.start()
        return {"status": 201, "message": "Created"}
        # package_build_process.delay(project, PROJECTS_DATA[project]["repo"],
        #                       "master",
        #                       path_to_missile=PROJECTS_DATA[project]["path_to_missile"],
        #                       domain=domain, stack=stack)

    def get(self, project):
        return "NotImplementedBroException"

class PackageList(BaseResource):
    def get(self):
        return {"packages": self.backend.list_packages()}

class Package(BaseResource):
    def get(self, package):
        self.reqparse.add_argument("version", type=str)
        args = self.reqparse.parse_args()
        version = args["version"]
        package = self.backend.get_package(package, version=version)
        if not package:
            abort(404, status=404, message="Not Found", info="Package not found")
        return package if not version else {version: package}

class LockList(BaseResource):

    def get(self):
        return {"locks": self.backend.list_locks()}

    def delete(self):
        self.reqparse.add_argument("type", type=str)
        self.reqparse.add_argument("name", type=str)
        args = self.reqparse.parse_args()
        type_, name = args["type"], args["name"]
        self.backend.delete_lock(type_, name)
        return flask.Response(status=204)


RESOURCES = [
    (DomainList, "/api/domains/"),
    (Domain, "/api/domains/<string:domain>"),
    (StackList, "/api/domains/<string:domain>/stacks/"),
    (Stack, "/api/domains/<string:domain>/stacks/<string:stack>"),
    (Build, "/api/builds/<string:project>"),
    (PackageList, "/api/packages/"),
    (Package, "/api/packages/<string:package>"),
    (LockList, "/api/locks/"),
]

def add_resources(api):
    for resource in RESOURCES:
        api.add_resource(*resource)
