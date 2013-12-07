import os
import unittest

import redis

from boby.lib.backends import RedisBackend

from tests import config_test

try:
    redis.Redis(config_test.REDIS_HOST, config_test.REDIS_PORT).keys()
    REDIS_OK = True
except Exception as e:
    import sys
    sys.stderr.write(str(e))
    REDIS_OK = False


@unittest.skipUnless(REDIS_OK, "REDIS is not there")
class BackendsDomainTestCase(unittest.TestCase):
    def cleanup(self):
        redis = self.backend.redis
        keys = redis.keys("domains:_test*")
        if keys:
            redis.delete(*keys)

    def setUp(self):
        self.backend = RedisBackend(redis_host=config_test.REDIS_HOST,
                                    redis_port=config_test.REDIS_PORT)
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def test_domain_defaults(self):
        keys = ["last_stack_version", "last_deployed_staging",
                "last_deployed_live", "available_packages"]
        for k in self.backend.domain_defaults:
            self.assertTrue(k in keys)

    def test_exists_create(self):
        self.assertFalse(self.backend.domain_exists("_test-a-domain"))
        self.backend.create_domain("_test-a-domain")
        self.assertTrue(self.backend.domain_exists("_test-a-domain"))
        self.assertTrue(self.backend.get_domain("_test-a-domain"))


class BackendsStackTestCase(unittest.TestCase):
    def setUp(self):
        self.backend = RedisBackend()

    def test_stack_defaults(self):
        defaults = self.backend.stack_defaults
        meta_keys = ["created_by", "created_at", "stable",
                     "deployed_staging_at", "deployed_live_at"]
        self.assertTrue("meta" in defaults and "packages" in defaults)
        for k in self.backend.stack_defaults["meta"]:
            self.assertTrue(k in meta_keys)
