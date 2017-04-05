import os
import sys
import json

from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../")

import pytest

from flasky.parameters import (
        ParameterResolver,
        QueryParameter,
        CollectionQueryParameter,
        ParameterRequiredError,
        BodyArgument,
        CollectionBodyArgument,
        JSONPathArgument
    )


mock_app = MagicMock()


@pytest.mark.asyncio
async def test_bind_params_should_create_parameters_namespace_in_handler():
    resolver = ParameterResolver(mock_app)
    method_definition = {
                "params": [
                        QueryParameter("test_param")
                    ]
                }
    handler = MagicMock()
    handler.get_query_argument = lambda x, default=None: "test_value"
    resolver.bind_params(handler, method_definition)


    assert handler.parameters is not None
    assert handler.parameters.test_param is not None


def test_query_parameter_resolve_should_extract_value_from_handler():
    param = QueryParameter("test")
    handler = MagicMock()
    handler.get_query_argument = MagicMock()
    handler.get_query_argument.return_value = "test_val"

    assert param.resolve(handler )== "test_val"


def test_query_parameter_resolve_should_raise_parameter_required_error_when_param_is_required():
    param = QueryParameter("test_param_1", is_required=True)
    handler = MagicMock()
    handler.get_query_argument.return_value = None

    try:
        param.resolve(handler)
    except ParameterRequiredError:
        assert True
        return

    assert False

def test_query_parameter_resolve_should_resolve_none_when_param_is_not_required_and_not_exists():
    param = QueryParameter("test_param_2")
    handler = MagicMock()
    handler.get_query_argument = lambda x,default=None: None


    assert param.resolve(handler) is None

def test_query_parameter_resolve_should_parse_parameter_by_its_type():
    handler = MagicMock()
    handler.get_query_argument = lambda x, default=None: "True"

    param = QueryParameter("test_param", typ=bool)
    assert param.resolve(handler) == True

def test_collection_query_parameter_resolve_should_return_list_of_values_when_handler_contains_values():
    handler = MagicMock()
    handler.get_arguments = lambda x, strip=True: ["a","b"]

    param = CollectionQueryParameter("letters")

    assert param.resolve(handler) == ["a", "b"]

def test_collection_query_parameter_resolve_should_return_bool_values_when_handler_contains_true_as_str():
    handler = MagicMock()
    handler.get_arguments.return_value = ["True", "True"]

    param = CollectionQueryParameter("letters", mapper=bool)

    assert param.resolve(handler) == [True, True]

def test_body_parameteR_resolve_should_return_value_in_its_type():
    handler = MagicMock()
    handler.get_body_argument.return_value = "20"
    param = BodyArgument("test_param", typ=int)

    assert param.resolve(handler) == 20

def test_body_collection_parameter_resolver_should_return_values():
    handler = MagicMock()
    handler.get_body_arguments.return_value = ["test", "test2"]

    param = CollectionBodyArgument("test_param")

    assert param.resolve(handler) == ['test', 'test2']

def test_resolve_of_json_path_argument_should_return_body_as_json_when_path_is_none():
    handler = MagicMock()
    handler.body_as_json.return_value = {"hello":"world"}
    param = JSONPathArgument("test_param").resolve(handler)
    assert param["hello"] == "world"


def test_json_path_argument_resolve_nested_argument():
    handler = MagicMock()
    body_json = json.dumps({
            "hello": {
                "world":"merhaba"
                }
        }).encode("utf-8")

    handler.body_as_json.return_value = json.loads(body_json.decode("utf-8")) 
    handler.request.body = body_json
    path_arg = JSONPathArgument("test_param", path="hello.world").resolve(handler)

    assert path_arg == "merhaba"


def get_handler_without_json_body():
    handler = MagicMock()
    handler.body_as_json.return_value = None
    handler.request.body = "not=json&body=input".encode("utf-8")
    return handler


def test_json_path_argument_resolve_should_not_raise_exception_if_json_body_not_exist_and_not_required():
    handler = get_handler_without_json_body()
    path_arg = JSONPathArgument("test_param", path="hello.world").resolve(handler)

    assert path_arg == None


def test_json_path_argument_resolve_should_raise_exc_if_param_is_required():
    handler = get_handler_without_json_body()
    try:
        path_arg = JSONPathArgument("test_param", path="hello.world", 
                                    is_required=True).resolve(handler)

    except ParameterRequiredError:
        assert True
        return
    assert False, "Exception did not raised"


def test_json_path_argument_resolve_should_return_default_val_if_its_not_found():
    handler = MagicMock()
    handler.body_as_json.return_value = {
                "test":"val"
            }

    path_arg = JSONPathArgument("test_param", path="test_2", is_required=False, default="default_val")
    path_val = path_arg.resolve(handler)
    assert path_val == "default_val"

class StubModel(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def from_dict(cls, d):
        return StubModel(**d)


def test_json_path_argument_should_return_value_mapped_with_mapper():
    handler = MagicMock()
    handler.body_as_json.return_value = {
                        "params": {
                                "model" : {
                                        "test_key": "test_val"
                                }
                            }
                        }

    path_val = JSONPathArgument("test_param", path="params.model",
                                is_required=True, mapper=StubModel.from_dict).resolve(handler)

    assert path_val.test_key == "test_val"

    

