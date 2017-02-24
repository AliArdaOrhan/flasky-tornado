import datetime
import functools
from asyncio import iscoroutinefunction, get_event_loop
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from tornado.log import enable_pretty_logging
from tornado.web import Application
from tornado.ioloop import IOLoop
from jsonschema import Draft4Validator, FormatChecker

from flasky import ConfigurationError, BadRequestError
from flasky.handler import DynamicHandler
from flasky.parameter import JSONParameterResolver, JSONParam


class FlaskyApp(object):
    executor = ThreadPoolExecutor()
    def __init__(self, ioloop=None, **settings):
        self.ioloop = ioloop
        if not ioloop:
            self.ioloop = get_event_loop()
        self.before_request_funcs = []
        self.after_request_funcs = []
        self.user_loader_func = None
        self.endpoints = OrderedDict()
        self.error_handlers = {}
        self.app = None
        self.settings = settings

    def api(self, endpoint=None, method=None, params=None, json_schema=None, requires_role=None, host='.*$'):

        def decorator(f):
            if not iscoroutinefunction(f):
                raise ConfigurationError(message="Function [{}] should be coroutine in order to use."
                                         .format(f.__name__))
            if not endpoint:
                raise ConfigurationError(message='Endpoint should be provided.')

            if not method:
                raise ConfigurationError(message='Method should be provided')

            if method not in DynamicHandler.SUPPORTED_METHODS:
                raise ConfigurationError(message='Unsuppoterted method {}'.format(method))

            endpoint_definition = self.endpoints.get('endpoint', None)
            if not endpoint_definition:
                endpoint_definition = {k: {} for k in DynamicHandler.SUPPORTED_METHODS}
                self.endpoints[endpoint] = endpoint_definition

            method_definition = {
                'function': f,
                'parameters': self._prepare_parameter_resolvers(params),
                'json_schema': self._prepare_schema_validator(json_schema),
                'requires_role': requires_role
            }

            endpoint_definition[method] = method_definition

            return f

        return decorator

    def user_loader(self, f):
        self.user_loader_func = f
        return f

    def before_request(self, f):
        self.before_request_funcs.append(f)
        return f

    def after_request(self, f):
        self.after_request_funcs.append(f)
        return f

    def run(self, port=8888):
        enable_pretty_logging()
        self.app = Application(**self.settings)

        for endpoint in self.endpoints:
            spec = self._create_dynamic_handlers(endpoint)
            self.app.add_handlers(*spec)

        self.app.listen(port)
        IOLoop.current().start()

    def _create_dynamic_handlers(self, endpoint_pattern):
        endpoint = self.endpoints[endpoint_pattern]
        return '.*$', [
            (endpoint_pattern, DynamicHandler, dict(endpoint_definition=endpoint, endpoint=endpoint, user_loader_func=self.user_loader_func,
                                                    after_request_funcs=self.after_request_funcs,
                                                    before_request_funcs=self.before_request_funcs, run_in_executor=self.run_in_executor))]

    def _prepare_parameter_resolvers(self, params):
        if not params:
            return

        return {param: JSONParameterResolver(param.param_path) for param in params}

    def _prepare_schema_validator(self, json_schema):
        if not json_schema:
            return
        return functools.partial(validate_schema, json_schema)

    def errorhandler(self, err_type):
        def decorator(f):
            self.error_handlers[err_type] = f
            return f
        return decorator

    def run_in_executor(self, func, *args):
        return self.ioloop.run_in_executor(self.executor, functools.partial(func, *args))

def validate_schema(schema, data):
    validator = Draft4Validator(
        schema,
        types={"datetime": datetime.datetime},
        format_checker=FormatChecker())

    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        message = ""
        for error in errors:
            message += str(error.message) + ", "
        raise BadRequestError(message=message)