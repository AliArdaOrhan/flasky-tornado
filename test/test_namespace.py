import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__) + '/../'))

from flasky.helpers import _HandlerBoundObject


def test_getattr_should_return_none_when_accessing_a_property():
    n = _HandlerBoundObject()
    assert n.n == None

def test_getattr_should_return_parameter_itself_when_parameter_is_define():
    n = _HandlerBoundObject(k="Hello")
    assert n.k == "Hello"



