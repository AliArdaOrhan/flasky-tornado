import os
import sys
import json

from tornado.platform.asyncio import AsyncIOMainLoop

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../")

from flasky.app import FlaskyApp
from flasky.parameters import (QueryParameter,
                               CollectionQueryParameter,
                               JSONPathArgument
                               )

AsyncIOMainLoop().install()

app = FlaskyApp()


@app.api(
    endpoint="/hello",
    method="GET",
    params = [
        QueryParameter("test", is_required=True, typ=str),
        CollectionQueryParameter("test_col", mapper=str)]

)
async def hello_world(handler, *args, **kwargs):
    if hasattr(handler, "context"):
        handler.write("Handler has context object \n")

    if hasattr(handler.context, "stub_service"):
        handler.write("Handler has stub service \n")

    if hasattr(handler.context, "parameters"):
        handler.write("Handler has a parameter test value<{}> \n"
                .format(handler.context.parameters.test))

    test_col = handler.context.parameters.test_col or []
    for val in test_col:
        print(val)

@app.api(
    endpoint="/hello",
    method="POST",
    params = [
        JSONPathArgument("name", path="customer.name", is_required=True),
        JSONPathArgument("bobody")]
)
async def hello_world_2(handler, *args, **kwargs):
    body = handler.body_as_json()

    print(handler.context.parameters.name)
    print(handler.context.parameters.bobody)
    print(handler.context.stub_service)
    print(handler.context.db)



@app.di.register()
async def stub_service():
    return StubService()

@app.di.register(name="db")
async def d_b(stub_service):
    return StubService()


class StubService(object):
    pass


app.run(8888)
