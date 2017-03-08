import functools
from asyncio import iscoroutinefunction, get_event_loop
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from tornado.web import Application, StaticFileHandler
from tornado.ioloop import IOLoop, PeriodicCallback

from flasky.errors import ConfigurationError, default_error_handler_func
from flasky.handler import DynamicHandler


class FlaskyApp(object):

    def __init__(self, ioloop=None, **settings):
        self.on_start_funcs = []

        self.ioloop = ioloop
        if not ioloop:
            self.ioloop = get_event_loop()
        self.before_request_funcs = []
        self.after_request_funcs = []
        self.teardown_request_funcs = []
        self.user_loader_func = None
        self.host_definitions = {}
        self.endpoints = OrderedDict()
        self.error_handlers = {}
        self.settings = settings
        self.option_files = []
        self.app = None
        self.static_file_handler_definitions = []
        self.periodic_functions = []

        if settings['executor_type'] == 'process':
            self.executor = ProcessPoolExecutor(max_workers=(settings['max_worker_count'] or 1))
        else:
            self.executor = ThreadPoolExecutor(max_workers=(settings['max_worker_count'] or 1))


        self.is_builded = False


    def api(self, host='.*$', endpoint=None, method=None, **kwargs):
        host_definition = self.host_definitions.get(host, None)
        if host_definition == None:
            host_definition = {}
            self.host_definitions[host] = host_definition

        endpoint_definition = self.host_definitions.get(host).get(endpoint, None)
        if endpoint_definition == None:
            endpoint_definition = {supported_method: {} for supported_method in DynamicHandler.SUPPORTED_METHODS}
            host_definition[endpoint] = endpoint_definition

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

            self.host_definitions[host][endpoint][method] = {
                'function': f
            }

            self.host_definitions[host][endpoint][method].update(kwargs)
            return f

        return decorator

    def user_loader(self, f):
        self.user_loader_func = f
        return f

    def before_request(self, f):
        if not f:
            raise ValueError('Function cant be none')
        self.before_request_funcs.append(f)
        return f

    def after_request(self, f):
        self.after_request_funcs.append(f)
        return f

    def on_teardown_request(self, f):
        self.teardown_request_funcs.append(f)
        return f

    def serve_static_file(self, pattern, path):
        if not pattern:
            raise ValueError('Pattern should be specified...')

        if path == None:
            raise ValueError('Path should be specified.')

        self.static_file_handler_definitions.append((pattern, {
            'path': path
        }))

    def build_app(self, host="0.0.0.0"):
        self.app = Application(default_host=host, **self.settings)

        for host, host_definition in self.host_definitions.items():
            for endpoint, endpoint_definition in host_definition.items():
                handler = self._create_dynamic_handlers(host, endpoint, endpoint_definition)
                self.app.add_handlers(*handler)

        for url_patttern, static_file_handler_settings in self.static_file_handler_definitions:
            self.app.add_handlers(".*$", [(url_patttern, StaticFileHandler, static_file_handler_settings)])

        if not self.error_handlers.get(None, None):
            self.error_handlers[None] = default_error_handler_func

        self.is_builded = True

    def run(self, port=8888, host="0.0.0.0"):
        if not self.is_builded:
            self.build_app(host=host)
        self.app.listen(port)
        for on_start_func in self.on_start_funcs:
            IOLoop.current().add_callback(on_start_func)

        IOLoop.current().start()

    def _create_dynamic_handlers(self, host, endpoint, endpoint_definition):
        return host, [
            (endpoint, DynamicHandler, dict(endpoint_definition=endpoint_definition, endpoint=endpoint, user_loader_func=self.user_loader_func,
                                                    after_request_funcs=self.after_request_funcs, error_handler_funcs=self.error_handlers,
                                                    before_request_funcs=self.before_request_funcs, run_in_executor=self.run_in_executor,
                                            teardown_request_funcs=self.teardown_request_funcs))]

    def run_in_executor(self, func, *args):
        return self.ioloop.run_in_executor(self.executor, functools.partial(func, *args))

    def run_periodic(self, func_time, func, *args):
        cb = PeriodicCallback(functools.partial(func, *args), func_time)
        cb.start()
        self.periodic_functions.append(cb)

    def on_start(self, f):
        self.on_start_funcs.append(f)
        return f

    def error_handler(self, err_type=None):
        def decorator(f):
            self.error_handlers[err_type] = f
            return f

        return decorator

    def add_tornado_handler(self, host_pattern, host_handlers):
        self.app.add_handlers(host_pattern, host_handlers)





