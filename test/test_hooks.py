from flasky.app import FlaskyApp
from unittest.mock import MagicMock
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase
from tornado.platform.asyncio import AsyncIOMainLoop

if not hasattr(IOLoop, "_instance"):
    AsyncIOMainLoop().install()


class TestBeforeRequestMethods(AsyncHTTPTestCase):

    def setUp(self):
        super().setUp()
        self.before_request_func_mock = MagicMock()

    def get_app(self):
        app = FlaskyApp()

        @app.api(
            endpoint="/api/test",
            method="GET"
        )
        async def get_method(handler):
            handler.set_status(200)

        @app.before_request
        async def before_request_func(handler, definition):
            self.before_request_func_mock()

        app.build_app()
        return app.app

    #: BRF = Before request function
    def test_brf1_executed(self):
        self.fetch("/api/test")
        self.before_request_func_mock.assert_any_call()


class TestAfterRequestMethods(AsyncHTTPTestCase):

    def setUp(self):
        super().setUp()
        self.after_request_func_mock = MagicMock()

    def get_app(self):
        app = FlaskyApp()

        @app.api(
            endpoint="/api/test",
            method="GET"
        )
        async def get_method(handler):
            handler.set_status(200)

        @app.after_request
        async def after_request_func(handler, definition):
            self.after_request_func_mock()

        app.build_app()
        return app.app

    def test_afr1_executed(self):
        self.fetch("/api/test")
        self.after_request_func_mock.assert_any_call()


class TestErrorHandlerFunctionIfExceptionOccurs(AsyncHTTPTestCase):

    def setUp(self):
        super().setUp()
        self.error_handler_func_mock = MagicMock()
        self.after_request_func_mock = MagicMock()
        self.teardown_request_func_mock = MagicMock()

    def get_app(self):
        app = FlaskyApp()

        @app.api(
            endpoint="/api/test",
            method="GET"
        )
        async def get_method(handler, *args, **kwargs):
            raise ValueError

        @app.error_handler(ValueError)
        async def handle_error(handler, exc, definition):
            self.error_handler_func_mock()

        @app.after_request
        async def this_should_not_be_executed(handler, definition):
            self.after_request_func_mock()

        @app.on_teardown_request
        async def this_should_be_executed(handler, definition):
            self.teardown_request_func_mock()

        app.build_app()
        return app.app

    def test(self):
        self.fetch("/api/test")
        self.error_handler_func_mock.assert_any_call()
        self.after_request_func_mock.assert_not_called()
        self.teardown_request_func_mock.assert_any_call()


class CustomExc(BaseException):
    pass


class TestDefaultErrorHandler(AsyncHTTPTestCase):

    def setUp(self):
        super().setUp()
        self.error_handler_func_mock = MagicMock()

    def get_app(self):
        app = FlaskyApp()

        @app.api(
            endpoint="/api/test",
            method="GET"
        )
        async def get_method(handler):
            raise CustomExc

        @app.error_handler(CustomExc)
        async def handle_custom_exc(handler, exc, definition):
            self.error_handler_func_mock()

        app.build_app()
        return app.app

    def test(self):
        self.fetch("/api/test")
        self.error_handler_func_mock.assert_any_call()
