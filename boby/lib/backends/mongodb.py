import pymongo
from nanomongo import Index, Field, BaseDocument

from .base import BaseBackend

client = pymongo.MongoClient()


class Domain(BaseDocument, dot_notation=True, client=client, db="boby"):
    _id = Field(str)
    last_stack_version = Field(str, default="")
    available_packages = Field(list, default=list)

    @property
    def staging_deployments(self):
        pass

    @property
    def live_deployments(self):
        pass


class Stack(BaseDocument, dot_notation=True, client=client, db="boby"):
    _id = Field(str)
    domain = Field(str, required=True)
    created_by = Field(str, default="DevOps Engineer")
    created_at = Field(datetime.datetime, default=datetime.datetime.utcnow)
    stable = Field(bool, default=False)
    frozen = Field(bool, default=False)
    deployed_staging_at = Field(datetime.datetime)
    deployed_live_at = Field(datetime.datetime)
    packages = Field(dict, default=dict)


class Build(BaseDocument, dot_notation=True, client=client, db="boby"):
    created_by = Field(str)
    created_at = Field(datetime.datetime)
    branch = Field(str)
    commit = Field(str)


class Deployment(BaseDocument, dot_notation=True, client=client, db="boby"):
    env = Field(str)  # staging, live
    domain = Field(str)
    stack = Field(str)
    deployed_by = Field(str)
    deployed_at = Field(datetime.datetime, default=datetime.datetime.utcnow)


class Package(BaseDocument, dot_notation=True, client=client, db="boby"):
    name = Field(str, required=True)
    version = Field(str, required=True)
    filename = Field(str, required=True)


class Lock(BaseDocument, dot_notation=True, client=client, db="boby"):
    lock_type = Field(str, required=True)
    name = Field(str, required=True)
    created_at = Field(datetime.datetime, default=datetime.datetime.utcnow)


class MongoBackend(BaseBackend):
    """Handle MongoDB operations"""
    def __init__(self):
        # TODO move register here
        pass

    # DOMAINS
    def domain_exists(self, domain):
        return True if Domain.find_one(domain) else False

    def create_domain(self, domain):
        if self.domain_exists(domain):
            raise TypeError("Domain '%s' exists" % domain)
        Domain(_id=domain).insert()

    def get_domain(self, domain):
        return Domain.find_one(domain)

    def update_domain(self, domain, **kwargs):
        d = self.get_domain(domain)
        for k, v in kwargs.items():
            d[k] = v
        d.save()

    def list_domains(self):
        return Domain.find()

    # STACKS
    def stack_exists(self, domain, stack):
        return True if Stack.find_one({"domain": domain, "stack": stack}) else False

    def create_stack(self, domain, stack):
        if self.stack_exists(domain, stack):
            raise TypeError("Stack 'domains:%s:stacks:%s' exists" % (domain, stack))
        if not self.domain_exists(domain):
            raise TypeError("Domain '%s' does not exist" % domain)
        Stack(_id=stack, domain=domain).insert()

    def get_stack(self, domain, stack):
        return Stack.find_one({"domain": domain, "stack": stack})

    def update_stack(self, domain, stack, **kwargs):
        s = self.get_stack(domain, stack)
        for k, v in kwargs.items():
            s[k] = v
        s.save()

    def list_stacks(self, domain, detail=None):
        if detail:
            return Stack.find({"domain": domain}).sort("created_at", -1)
        return Stack.find({"domain": domain}, fields=["_id"]).sort("created_at", -1)

    def copy_stack_packages(self, domain=None, source=None, dest=None):
        assert (domain and source and dest), "domain, source, dest are required kwargs"
        assert source != dest, "Source and destination are the same, '%s'" % source
        d_stack = self.get_stack(domain, dest)
        if d_stack.frozen:
            raise TypeError("Dest. stack: %s:%s is frozen" % (d_stack.domain, d_stack._id))
        s_stack = self.get_stack(domain, source)
        self.update_stack(domain, dest, packages=s_stack["packages"])

    # PACKAGES
    def package_exists(self, package, version):
        return True if Package.find_one({"name": package, "version": version}) else None

    def create_package(self, package, version, filename):
        if self.package_exists(package, version):
            raise TypeError("Package '%s:%s' exists" % (package, version))
        Package(name=package, version=version, filename=filename).insert()

    def get_package(self, package, version=None):
        if version:
            return Package.find_one({"name": package, "version": version})
        return Package.find({"name": package}).sort("version", -1)

    def list_packages(self):
        plist = []
        for package in Package.find(fields=["name"]):
            if package.name not in plist:
                plist.append(package.name)
        return plist

    def available_packages(self, domain):
        d = self.get_domain(domain)
        if not d:
            raise TypeError("Domain '%s' does not exist" % domain)
        return d.available_packages

    def add_stack_package(self, domain, stack, pkg_name, pkg_version):
        s = self.get_stack(domain, stack)
        if not s:
            raise TypeError("Stack %s:%s does not exist" % (domain, stack))
        s.packages[pkg_name] = pkg_version
        s.save()

    def get_latest_version(self, package):
        plist = Package.find({"name": package}, fields="version").sort("version", -1).limit(1)
        if plist:
            return plist[0].version
        return ""

    # BUILDS

    # LOCKS
    def lock_exists(self, type_, name):
        return True if Lock.find_one({"lock_type": type_, "name": name}) else False

    def create_lock(self, type_, name):
        if self.lock_exists(type_, name):
            raise TypeError("Lock '%s:%s' exists" % (type_, name))
        Lock(lock_type=type_, name=name).insert()

    def list_locks(self):
        locks = {}
        for lock in Lock.find().sort("created_at", -1):
            if lock.lock_type not in locks:
                locks[lock_type] = []
            locks[lock_type].append(lock)

    def delete_lock(self, type_, name):
        Lock.get_collection().remove({"lock_type": type_, "name": name})
