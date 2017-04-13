import unittest
import datetime

from flasky.cache import CacheManager, Cache
from tornado.testing import AsyncTestCase, gen_test


class TestCacheManager(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.app_mock = unittest.mock.MagicMock()
        self.ioloop_mock = unittest.mock.MagicMock()

    def test_register_should_increase_cache_count_by_one(self):
        manager = CacheManager(self.app_mock, ioloop=self.ioloop_mock)

        @manager.register(cache_name="test", interval=10000)
        async def test_cache():
            return {"entry": "entry"}

        self.assertEquals(len(manager.caches), 1)

    def test_before_request_hook_should_create_cache_context_on_handler(self):
        manager = CacheManager(self.app_mock, ioloop=self.ioloop_mock)

        @manager.register(cache_name="test", interval=10000)
        async def test_cache_1():
            return {"entry": "entry"}

        handler_mock = unittest.mock.MagicMock()
        handler_mock.context = unittest.mock.MagicMock()
        handler_mock.context.cache = None

        manager.before_request_hook(handler_mock, {})
        self.assertIsNotNone(handler_mock.context.cache)


class TestCache(AsyncTestCase):

    def test_is_running_should_return_false(self):
        cache = Cache(
                "test", lambda: {}, 1000,
                ioloop=unittest.mock.MagicMock(),
                app=unittest.mock.MagicMock())

        self.assertFalse(cache.is_running())

    @unittest.mock.patch.object(Cache, "_create_periodic_callback")
    def test_run_create_call_start_of_periodic_callback_obj(self, mock_func):
        cache_loader_func_mock = unittest.mock.MagicMock()
        periodic_callback_mock = unittest.mock.MagicMock()

        mock_func.return_value = periodic_callback_mock
        cache = Cache(
                "test", cache_loader_func_mock, 1000,
                run_immediate=True,
                ioloop=unittest.mock.MagicMock(),
                app=unittest.mock.MagicMock())

        cache.run()
        periodic_callback_mock.start.assert_any_call()

        cache.stop()
        periodic_callback_mock.stop.assert_any_call()

    @gen_test
    async def test_run_cache_func_should_update_stats_of_cache(self):
        async def test():
            return {"test": "value"}

        cache = Cache(
                "test", lambda: {}, 1000,
                ioloop=unittest.mock.MagicMock(),
                app=unittest.mock.MagicMock())

        wrapped = cache._wrap_func(test)
        await wrapped()

        self.assertEquals(cache.stats["total_run_count"], 1)
        self.assertEquals(
                type(cache.stats["last_run_time"]), datetime.datetime)
        self.assertEquals(cache.stats["last_item_count"], 1)
        self.assertNotEquals(cache.stats["last_run_duration"], 0)
        self.assertNotEquals(cache.stats["overall_duration"], 0)
