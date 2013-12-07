import datetime


class BaseBackend(object):
    """Defaults for backends"""

    @property
    def is_redis(self):
        return self.__class__.__name__ == "RedisBackend"

    @property
    def is_mongo(self):
        return self.__class__.__name__ == "MongoBackend"

    def domain_defaults(self, **kwargs):
        if self.is_redis:
            return dict(
                last_stack_version="",
                last_deployed_staging="",
                last_deployed_live="",
                available_packages=[],
            )
        elif self.is_mongo:
            return dict(
                {
                    "_id": "",
                    "last_stack_version": "",
                    "available_packages": [],
                }, **kwargs
            )

    def stack_defaults(self, **kwargs):
        if self.is_redis:
            return dict(
                meta={
                    "created_by": "DevOps Engineer",
                    "created_at": datetime.datetime.utcnow().isoformat(),
                    "stable": False,
                    "deployed_staging_at": "Never",
                    "deployed_live_at": "Never",
                },
                packages={},
        )
        elif self.is_mongo:
            return dict(
                {
                # _id is auto by MongoDB
                    "domain": "",
                    "version": "",
                    "created_by": "DevOps Engineer",
                    "created_at": datetime.datetime.utcnow(),
                    "stable": False,
                    "frozen": False,
                    "deployed_staging_at": None,
                    "deployed_live_at": None,
                    "packages": {},
                }, **kwargs
            )

    def build_defaults(self, **kwargs):
        if self.is_redis:
            return dict(
                created_by="DevOps Engineer",
                created_at=datetime.datetime.utcnow().isoformat(),
                branch="",
                commit="",
            )
        elif self.is_mongo:
            return dict(
                {
                    # _id is auto by MongoDB
                    "created_by": "DevOps Engineer",
                    "created_at": datetime.datetime.utcnow(),
                    "branch": "",
                    "commit": "",
                }, **kwargs
            )

    def deployment_defaults(self, **kwargs):
        if self.is_mongo:
            return dict(
                {
                    # _id is auto by MongoDB
                    "env": "",
                    "domain": "",
                    "stack": "",
                    "deployed_by": "",
                    "deployed_at": datetime.datetime.utcnow(),
                }, **kwargs
            )

    def package_defaults(self, **kwargs):
        if self.is_mongo:
            return dict(
                {
                    "name": "",
                    "version": "",
                    "filename": "",
                }, **kwargs
            )

    def lock_defaults(self, **kwargs):
        if self.is_mongo:
            return dict(
                {
                    "type": "",
                    "name": "",
                    "created_at": datetime.datetime.utcnow(),
                }, **kwargs
            )
