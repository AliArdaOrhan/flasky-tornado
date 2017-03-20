import sys
import os

import pytest
from unittest.mock import MagicMock

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from flasky.di import DIContainer, PROTOTYPE
from flasky.errors import ConfigurationError
from flasky.app import FlaskyApp

app = MagicMock()


def test_factory_decorator_should_increase_object_count():
    di = DIContainer(app)

    @di.register()
    async def create_db():
        return dict(dv="db")

    assert di.get("create_db") is not None

@pytest.mark.asyncio
async def test_get_should_execute_factory_function_when_called_with_factory_func_name(event_loop):

    di = DIContainer(app)

    is_executed = {"value":False}

    @di.register()
    async def settings():
        is_executed["value"] = True
        return dict(key1="val1", key2="val2")

    await di.get("settings")

    assert is_executed["value"] == True

class StubDB(object):
    pass

@pytest.mark.asyncio
async def test_get_should_return_object_instance():

    di = DIContainer(app)

    @di.register()
    async def db():
        return StubDB()

    db = await di.get("db")

    assert type(db) == StubDB


@pytest.mark.asyncio
async def test_get_should_return_same_instance_when_its_registered_singleton():
    di = DIContainer(app)

    @di.register()
    async def db():
        return StubDB()

    db_1 = await di.get('db')
    db_2 = await di.get('db')

    assert db_1 == db_2

@pytest.mark.asyncio
async def test_get_should_return_different_instances_when_its_registered_as_prototype():
    di = DIContainer(app)

    @di.register(strategy=PROTOTYPE)
    async def db():
        return StubDB()

    db_1 = await di.get('db')
    db_2 = await di.get('db')

    assert db_1 != db_2

@pytest.mark.asyncio
async def test_get_should_return_object_which_registered_by_different_name():
    di = DIContainer(app)

    @di.register(name="test_db")
    async def db():
        return StubDB()

    db = await di.get("test_db")

    assert db is not None

class StubService(object):

    def __init__(self, db, serv2):
        self.db = db
        self.serv2 = serv2

@pytest.mark.asyncio
async def test_get_should_return_and_inject_dependencies_of_object():
    di = DIContainer(app)

    @di.register()
    async def db():
        return StubDB()

    @di.register()
    async def stub_service(db):
        return StubService(db, None)

    service = await di.get('stub_service')

    assert service is not None
    assert service.db is not None

@pytest.mark.asyncio
async def test_get_should_inject_named_arguments():
    di = DIContainer(app)

    @di.register()
    async def db():
        return StubDB()

    @di.register()
    async def serv2(db):
        return StubService(db, None)

    @di.register()
    async def stub_service(serv2, db=None):
        return StubService(db, serv2)

    service = await di.get('stub_service')

    assert service is not None

    assert service.db is not None
    assert service.serv2 is not None

    assert service.db is await di.get('db')
    assert service.serv2 is await di.get('serv2')


@pytest.mark.asyncio
async def test_get_should_raise_exception_when_dependency_is_not_found():
    di = DIContainer(app)

    @di.register()
    async def stub_service(db):
        return StubService(None, db=db)

    try:
        await di.get('stub_service')
    except ConfigurationError as e:
        assert True
        return

    assert False

@pytest.mark.asyncio
async def test_get_should_raise_exception_when_circular_dependency_is_found():
    di = DIContainer(app)

    @di.register()
    async def first(second):
        return StubDB()

    @di.register()
    async def second(third):
        return StubDB()

    @di.register()
    async def third(first):
        return StubDB()
    try:
        await di.get('first')
    except ConfigurationError as e:
        assert True
        return

    assert False

class StubHandler(object):
    pass

@pytest.mark.asyncio
async def test_before_request_should_set_all_fields_of_handler():
    di = DIContainer(app)

    @di.register()
    async def mongo_client():
        return StubDB()

    @di.register()
    async def blu_db(mongo_client):
        return "venividivici"

    mock_handler = MagicMock()
    mock_handler.handler = StubHandler()
    mock_method_def = MagicMock()
    await di.before_request(mock_handler, mock_method_def)

    assert hasattr(mock_handler, "mongo_client")
    assert hasattr(mock_handler, "blu_db")
