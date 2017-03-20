import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__ + '/../')))

from flasky.app import FlaskyApp
import flasky.cache

logging.basicConfig(level=10)
app = FlaskyApp()

@app.cache.register(cache_name="contents", interval=5000, run_immediate=True)
async def contents():
    return ["Content1", "Content2"]


@app.api(
    endpoint="/cache_test",
    method="GET"
)
async def cache_test(handler, *args, **kwargs):
    handler.write("hello world")


app.run(8888)
