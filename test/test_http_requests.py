from flasky.app import FlaskyApp
from tornado.testing import AsyncHTTPTestCase
from tornado.platform.asyncio import AsyncIOMainLoop

AsyncIOMainLoop().install()


class TestHTTPMethods(AsyncHTTPTestCase):

    def get_app(self):
        app = FlaskyApp()

        @app.api(
            endpoint="/api/test",
            method="GET"
        )
        async def get_method(handler, *args, **kwargs):
            handler.set_status(200)

        @app.api(
            endpoint="/api/test",
            method="POST"
        )
        async def post_method(handler):
            handler.set_status(200)

        @app.api(
            endpoint="/api/test",
            method="PATCH"
        )
        async def patch_method(handler):
            handler.set_status(200)

        @app.api(
            endpoint="/api/test",
            method="DELETE"
        )
        async def delete_method(handler):
            handler.set_status(200)

        @app.api(
            endpoint="/api/test",
            method="PUT"
        )
        async def put_method(handler):
            handler.set_status(200)

        app.build_app()
        return app.app

    def test_get(self):
        res = self._do_fetch("GET")
        self.assertEquals(res.code, 200)

    def test_post(self):
        res = self._do_fetch("POST", body="helloworld")
        self.assertEquals(res.code, 200)

    def test_patch(self):
        res = self._do_fetch("PATCH", body="helloworld")
        self.assertEquals(res.code, 200)

    def test_delete(self):
        res = self._do_fetch("DELETE", body=None)
        self.assertEquals(res.code, 200)

    def test_put(self):
        res = self._do_fetch("PUT", body="helloworld")
        self.assertEquals(res.code, 200)

    def _do_fetch(self, method, body=None):
        return self.fetch("/api/test", method=method, body=body)
