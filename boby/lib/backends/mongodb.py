import pymongo

from .base import BaseBackend


# class Domain(BaseDocument, dot_notation=True, client=client, db="boby"):
#     _id = Field(str)
#     last_stack_version = Field(str, default="")
#     available_packages = Field(list, default=list)

#     @property
#     def staging_deployments(self):
#         pass

#     @property
#     def live_deployments(self):
#         pass


# class Stack(BaseDocument, dot_notation=True, client=client, db="boby"):
#     _id = Field(str)
#     domain = Field(str, required=True)
#     created_by = Field(str, default="DevOps Engineer")
#     created_at = Field(datetime.datetime, default=datetime.datetime.utcnow)
#     stable = Field(bool, default=False)
#     frozen = Field(bool, default=False)
#     deployed_staging_at = Field(datetime.datetime)
#     deployed_live_at = Field(datetime.datetime)
#     packages = Field(dict, default=dict)


# class Build(BaseDocument, dot_notation=True, client=client, db="boby"):
#     created_by = Field(str)
#     created_at = Field(datetime.datetime)
#     branch = Field(str)
#     commit = Field(str)


# class Deployment(BaseDocument, dot_notation=True, client=client, db="boby"):
#     env = Field(str)  # staging, live
#     domain = Field(str)
#     stack = Field(str)
#     deployed_by = Field(str)
#     deployed_at = Field(datetime.datetime, default=datetime.datetime.utcnow)


# class Package(BaseDocument, dot_notation=True, client=client, db="boby"):
#     name = Field(str, required=True)
#     version = Field(str, required=True)
#     filename = Field(str, required=True)


# class Lock(BaseDocument, dot_notation=True, client=client, db="boby"):
#     lock_type = Field(str, required=True)
#     name = Field(str, required=True)
#     created_at = Field(datetime.datetime, default=datetime.datetime.utcnow)


class MongoBackend(BaseBackend):
    """Handle MongoDB operations"""
    def __init__(self, *args, **kwargs):
        # TODO move register here
        super(MongoBackend, self).__init__(*args, **kwargs)
        self.mongo = pymongo.MongoClient()
        self.db = self.mongo[kwargs["db"]] if "db" in kwargs else self.mongo["boby"]
        self.domains = self.db["domain"]
        self.stacks = self.db["stack"]
        self.builds = self.db["build"]
        self.deployments = self.db["deployment"]
        self.packages = self.db["packages"]
        self.locks = self.db["locks"]

    # DOMAINS
    def domain_exists(self, domain):
        return True if self.domains.find_one(domain) else False

    def create_domain(self, domain):
        if self.domain_exists(domain):
            raise TypeError("Domain '%s' exists" % domain)
        self.domains.insert(self.domain_defaults(_id=domain))

    def get_domain(self, domain):
        return self.domains.find_one(domain)

    def update_domain(self, domain, **kwargs):
        d = self.get_domain(domain)
        for k, v in kwargs.items():
            d[k] = v
        self.domains.save(d)

    def list_domains(self):
        return self.domains.find()

    # STACKS
    def stack_exists(self, domain, stack):
        return True if self.stacks.find_one({"domain": domain, "version": stack}) else False

    def create_stack(self, domain, stack):
        if self.stack_exists(domain, stack):
            raise TypeError("Stack '%s:%s' exists" % (domain, stack))
        if not self.domain_exists(domain):
            raise TypeError("Domain '%s' does not exist" % domain)
        self.stacks.insert(self.stack_defaults(domain=domain, version=stack))

    def get_stack(self, domain, stack):
        return self.stacks.find_one({"domain": domain, "stack": stack})

    def update_stack(self, domain, stack, **kwargs):
        s = self.get_stack(domain, stack)
        for k, v in kwargs.items():
            s[k] = v
        self.stacks.save(s)

    def list_stacks(self, domain, detail=None):
        if detail:
            return self.stacks.find({"domain": domain}).sort("created_at", -1)
        query = self.stacks.find({"domain": domain}, fields=["version"])
        return map(lambda doc: doc["version"], query.sort("created_at", -1))

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
        return True if self.packages.find_one({"name": package, "version": version}) else None

    def create_package(self, package, version, filename):
        if self.package_exists(package, version):
            raise TypeError("Package '%s:%s' exists" % (package, version))
        self.packages.insert(self.package_defaults(name=package, version=version, filename=filename))

    def get_package(self, package, version=None):
        if version:
            return self.packages.find_one({"name": package, "version": version})
        return self.packages.find({"name": package}).sort("version", -1)

    def list_packages(self):
        plist = []
        for package in self.packages.find(fields=["name"]):
            if package.name not in plist:
                plist.append(package.name)
        return plist

    def available_packages(self, domain):
        d = self.get_domain(domain)
        if not d:
            raise TypeError("Domain '%s' does not exist" % domain)
        return d["available_packages"]

    def add_stack_package(self, domain, stack, pkg_name, pkg_version):
        s = self.get_stack(domain, stack)
        if not s:
            raise TypeError("Stack %s:%s does not exist" % (domain, stack))
        s.packages[pkg_name] = pkg_version
        self.stacks.save(s)

    def get_latest_version(self, package):
        plist = self.packages.find({"name": package}, fields=["version"]).sort("version", -1).limit(1)
        if plist:
            return plist[0].version
        return ""

    # BUILDS

    # LOCKS
    def lock_exists(self, type_, name):
        return True if self.locks.find_one({"lock_type": type_, "name": name}) else False

    def create_lock(self, type_, name):
        if self.lock_exists(type_, name):
            raise TypeError("Lock '%s:%s' exists" % (type_, name))
        self.locks.insert(self.lock_defaults(type=type_, name=name))

    def list_locks(self):
        locks = {}
        for lock in self.locks.find().sort("created_at", -1):
            if lock["type"] not in locks:
                locks[lock["type"]] = []
            locks[lock["type"]].append(lock)

    def delete_lock(self, type_, name):
        self.locks.remove({"type": type_, "name": name})
