import sys
import os

print(os.environ.keys())


from flasky.plugins.di import DIContainer


def test_factory_decorator_should_increase_object_count():
    di = DIContainer()
