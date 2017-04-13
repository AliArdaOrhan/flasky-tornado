from tornado.httpclient import AsyncHTTPClient
from tornado.testing import AsyncHTTPTestCase


class FlaskyTestCase(AsyncHTTPTestCase):

    is_initialized = False

    def setUp(self):
        super().setUp()
        self.client = AsyncHTTPClient()
        self.initialize()
        self.is_initialized = True

    def get_app(self):
        app = self.create_app()
        app.build_app()
        return app.app

    def create_app(self):
        raise NotImplemented
