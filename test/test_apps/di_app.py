import os
import sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

from tornado.platform.asyncio import AsyncIOMainLoop

ioloop = AsyncIOMainLoop()
ioloop.install()

from tornado.options import parse_command_line

from flasky.app import FlaskyApp
from flasky.di import DIContainer

app = FlaskyApp(debug=True)
di = DIContainer(app)


@app.api(
        endpoint="/",
        method="GET"
)
async def hello_world(handler, *args, **kwargs):
    handler.write("hello world")
    print(dir(handler))
    handler.lolo.write_hello(handler)

class LoLoObject(object):

    def write_hello(self, handler):
        handler.write("hello world from lolo")

@di.register()
async def lolo():
    return LoLoObject()


if __name__ == "__main__":
    parse_command_line()
    app.run(port=8888)
