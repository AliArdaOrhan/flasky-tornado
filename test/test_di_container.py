import unittest

from tornado.testing import AsyncTestCase, gen_test
from flasky.di import DIContainer
from flasky.errors import ConfigurationError


class DIContainerTest(AsyncTestCase):

    def setUp(self):
        super().setUp()
        self.app_mock = unittest.mock.MagicMock()

    def test_register_should_increase_registered_object_count(self):
        container = DIContainer(self.app_mock)

        @container.register()
        async def db():
            return {}

        self.assertEquals(container.registered_object_count, 1)

    @gen_test
    async def test_get(self):
        container = DIContainer(self.app_mock)

        @container.register()
        async def db():
            return {}

        @container.register()
        async def service(db):
            return {}

        @container.register()
        async def controller(service):
            return {}

        self.assertEquals(container.registered_object_count, 3)
        self.assertEquals(await container.get("controller"), {})

    @gen_test
    async def test_get_should_raise_circular_reference_detected_error(self):
        container = DIContainer(self.app_mock)

        @container.register()
        async def db(service):
            return {}

        @container.register()
        async def db_2(db):
            return {}

        @container.register()
        async def service(db_2):
            return {}

        try:
            await container.get("service")
        except ConfigurationError:
            self.assertTrue(True)
            return

        self.assertTrue(False)

    @gen_test
    async def test_before_request_should_set_di_attr_of_handler(self):
        handler_mock = unittest.mock.MagicMock()

        container = DIContainer(self.app_mock)

        @container.register()
        async def db():
            return {}

        await container.before_request_hook(handler_mock, {})

        self.assertIsNotNone(handler_mock.di)

    @gen_test
    async def test_on_start_hook_should_initialize_container(self):
        handler_mock = unittest.mock.MagicMock()

        container = DIContainer(self.app_mock)

        @container.register()
        async def db():
            return {}

        await container.on_start_hook({})
        self.assertEquals(container.object_count, 1)

        await container.before_request_hook(handler_mock, {})
        self.assertIsNotNone(handler_mock.di.db)

        try:
            await handler_mock.di.db2
        except ConfigurationError:
            return

        self.assertTrue(False)
