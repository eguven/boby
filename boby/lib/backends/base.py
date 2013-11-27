import datetime


class BaseBackend(object):
    """Defaults for backends"""

    @property
    def domain_defaults(self):
        return dict(
            last_stack_version="",
            last_deployed_staging="",
            last_deployed_live="",
            available_packages=[],
        )

    @property
    def stack_defaults(self):
        return dict(
            meta={
                "created_by": "Devops Engineer",
                "created_at": datetime.datetime.utcnow().isoformat(),
                "stable": False,
                "deployed_staging_at": "Never",
                "deployed_live_at": "Never",
            },
            packages={},
        )

    @property
    def build_defaults(self):
        return dict(
            created_by="Devops Engineer",
            created_at=datetime.datetime.utcnow().isoformat(),
            branch="",
            commit="",
        )
