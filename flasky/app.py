# -*- coding: utf-8 -*-
"""
    Flasky.app module implements the tornado.web.Application wrapper
"""

import functools
from asyncio import iscoroutinefunction, futures
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from tornado.web import Application, StaticFileHandler
from tornado.ioloop import IOLoop

from .errors import ConfigurationError, default_error_handler_func
from .handler import DynamicHandler
from .di import DIContainer
from .cache import CacheManager
from .scheduler import Scheduler
from .helpers import _HandlerBoundObject
from .parameters import ParameterResolver


class FlaskyApp(object):
    """The Bant object provides a convenient API to configure
    :class:`~tornado.web.Application` It acts as a container for all
    plugins, crosscutting concern functions, objects and settings.
    On invocation of run method, Bant instance registers
    :class:`~flasky.handler.DynamicHandler` classes for every endpoint that
    is defined by user.

    Bant instance might be created at the :file:`__init__.py` of your package.
    Another approach might be creating initialization closures to init
    API functions. For more information please refer to :ref: ::

        from bant import Bant
        app = Bant(**settings)


    :param ioloop: IOLoop that will be used by application. By default
                   Bant application uses :class:`asyncio.BaseEventLoop`

    :param settings: Application specific settings.

    """

    #: The class for used as object container
    #: See :class:`~flasky.DIContainer`
    #: TODO: This fill be deleted
    di_class = DIContainer

    #: The class for used as parameter resolver
    #: See :class: `~flasky.parameters.ParameterResolver`
    #: TODO: This will be deleted
    parameter_resolver_class = ParameterResolver

    #: The class for used as cache manager
    #: See :class: `~flasky.cache.CacheManager`
    #: TODO: This will be deleted
    cache_manager_class = CacheManager

    #: Default plugins which will be loaded at the initialization of FlaskyApp.
    #: Users might manipulate the value of this list and prevent the loading of
    #: module
    default_plugins = [
                "di",
                "parameters",
                "caches"
            ]

    #: The name of the logger to use.
    logger_name = "flasky.logger"

    def __init__(self, ioloop=None, **settings):

        #: :class:`tornado.ioloop.IOLoop` which will be used to run
        #: application. Default ioloop class is
        #: :class:`tornado.asyncio.AsyncIOMainLoop`
        self.ioloop = ioloop or self._get_ioloop()

        #: Please look :meth:`~build_app`
        self.is_builded = False

        #: The debug flag. This flag will be passed to tornado.Application
        #: If the debug flag set True, Application will be reload on every
        #: if code changes detected and Application will spit detailed
        #: logging information.
        self.debug = False

        #: Configuration dictionary, there might be better implementation for
        #: this in future versions
        self.settings = settings

        #: :class:`tornado.web.Application` instance for this flaskyApp.
        #: This instance will be injected to :class:`handler.DynamicHandler`
        #: TODO: change this variable name to tornado_app
        self.app = None

        #: List of functions which will be runned before any request
        #: will be handled. This functions might be used
        #: for any initialization routine
        self.on_start_funcs = []

        #: A list of functions which will be called at the beginning of the
        #: request. Before request functions can be used to perform common
        #: cross-cutting concerns (logging, authorization etc.)
        #: To register a function use the :meth:`before_request` decorator
        self.before_request_funcs = []

        #: A list of functions which will be called after the request handled
        #: by handler function. Function should take 2 parameters, a
        #: :class:`~tornado.web.RequestHandler` instance and endpoint
        #: definition.
        #:
        #: **Warning**: These functions will not be called if any error occurs
        #: during the execution of handler. To run piece of code after request
        #: in every circumstances please please check :meth:`teardown_request`
        #:
        #: To register a function use the :meth:`after_request` decorator
        self.after_request_funcs = []

        #: A list of functions which will be called after request is handled
        #: this function will be called even if any error exists on handler
        #: function. This method can :meth:`on_teardown_request`
        self.teardown_request_funcs = []

        #: A error specific handler registry. Key will be
        #: type of error and None type will be used as
        #: default error handler.
        #:
        #: To register an error handler, use the :meth:`error_handler`
        #: decorator
        self.error_handlers = {None: default_error_handler_func}

        #: Registered handler definitions
        #: All handlers registered under a tree which path might be accessed
        #: like this::
        #:
        #:      handler_function =
        #:          self.host_definitions['0.0.0.0']['/api/token']['POST']
        #:
        self.host_definitions = OrderedDict()

        #: Registered static file handlers, on build time this definitions
        #: will be converted to :class:`tornado.web.StaticFileHandler`. You
        #: can serve static file like this::
        #:
        #:      from flasky.app import FlaskyApp
        #:
        #:      app = FlaskyApp()
        #:      app.serve_static_file("/static/([^/]+)", "path/to/static/file")
        #:
        self.static_file_handler_definitions = []

        #: Executor which will be injected to handlers, max_worker_count of
        #: settings might be used to manage size of ThreadPoolExecutor.
        #: Default value is 1
        self.executor = ThreadPoolExecutor(
                max_workers=(settings.get('max_worker_count', None) or 1))

        #: Built-in plugins
        #: TODO: Implement plugin mechanisms
        self.di = self.di_class(self)
        self.parameter_resolver = self.parameter_resolver_class(self)
        self.cache = self.cache_manager_class(self)
        self.scheduler = Scheduler(self.ioloop)

    def _get_ioloop(self):
        from tornado.platform.asyncio import AsyncIOMainLoop
        if not hasattr(IOLoop, "_instance"):
            AsyncIOMainLoop().install()
        return IOLoop.current()

    def api(self, host='.*$', endpoint=None, method=None, **kwargs):
        """A decorator which will be used to register a handler for given
        endpoint. Parameters are default :class:`tornado.web.RequestHandler`
        parameters. Regexes can be used at endpoint definition and will be
        injected to as second parameter::

            @app.api(
                endpoint="/api/user",
                method="POST"
            )
            async def create_user(handler, *args, **kwargs):
                handler.write("hello world")

            @app.api(
                endpoint="api/user",
                method="GET"
            )
            async def get_users(handler, *args, **kwargs):
                handler.write({"user": "Asimov"})

        :param host: Host Address in which this handler function will be
                     registered.

        :param endpoint: Endpoint address for which this handler function
                         will be executed.

        :param method: HTTP Method(POST, GET, PUT etc..) for which
                       this handler function will be executed

        :param options:" Options that will be attached to handler function
                        all the way throught middleware pipeline
        """
        host_definition = self.host_definitions.get(host, None)
        if host_definition is None:
            host_definition = OrderedDict()
            self.host_definitions[host] = host_definition

        endpoint_definition = self.host_definitions[host].get(endpoint, None)
        if endpoint_definition is None:
            endpoint_definition = OrderedDict()
            for supported_method in DynamicHandler.SUPPORTED_METHODS:
                endpoint_definition[supported_method] = OrderedDict()
            host_definition[endpoint] = endpoint_definition

        def decorator(f):
            if not iscoroutinefunction(f):
                raise ConfigurationError(
                        message="Function [{}] should be"
                                "coroutine in order to use."
                                .format(f.__name__))

            if not endpoint:
                raise ConfigurationError(
                        message='Endpoint should be provided.')

            if not method:
                raise ConfigurationError(
                        message='Endpoint method(GET, POST etc..)'
                                'should be provided')

            if method not in DynamicHandler.SUPPORTED_METHODS:
                raise ConfigurationError(
                        message='Unsuppoterted method {}'.format(method))

            self.host_definitions[host][endpoint][method] = {
                'function': f
            }

            self.host_definitions[host][endpoint][method].update(kwargs)
            return f

        return decorator

    def on_start(self, f):
        """ Registers a function to be run on build time of application

        Function should take :class:BantApp as parameter. This is a good place
        to initialize the common objects, setting up logging vs::

            @app.on_start
            async def initialize(app):
                app.logger = logging.get("application_logger")

        """
        self.on_start_funcs.append(f)
        return f

    def before_request(self, f):
        """Registers a function to run before each request handler.

        Function should take 2 argument, an instance of
        :class:`~handler.DynamicHandler` and dictionary
        of endpoint definition::

            @app.before_request
            async def check_authorization(handler, handler_definition):
                if not handler.request.headers.get('Authorization', None):
                    raise UnauthorizedAccessError()
        """
        self.before_request_funcs.append(f)
        return f

    def after_request(self, f):
        """Registers a function to run after each request handler.

        Function should take 2 argument an instance of
        :class:`handler.DynamicHandler` and :type:`dict`
        of endpoint definition::

            @app.after_request
            async def add_cors_headers
                handler.set_header("Allow-Origin", "*")

        It's important to know that, if any error raised during pipeline,
        after request functions WILL NOT BE EXECUTED.

        To execute a function after pipeline in every circumstances, use
        :meth:`teardown_request`
        """
        self.after_request_funcs.append(f)
        return f

    def error_handler(self, err_type=None):
        """Registers a function for given error type.::

            @app.error_handler(MongoError)
            async def handle_mongo_error(handler, error, endpoint_definition):
                handler.clear()
                handler.write("Internal error occured")
                handler.set_status(500)

        :param err_type: an exception type which will be handled by this
                         error handler function. If given parameter is None,
                         handler will be used as default error handler.
        """
        def decorator(f):
            self.error_handlers[err_type] = f
            return f
        return decorator

    def on_teardown_request(self, f):
        self.teardown_request_funcs.append(f)
        return f

    def serve_static_file(self, pattern, path):
        """Serves matched files from given path:

        app.serve_static_file("*.png", "/path/to/png/files")
        """
        if not pattern:
            raise ValueError('Pattern should be specified...')

        if path is None:
            raise ValueError('Path should be specified.')

        self.static_file_handler_definitions.append((pattern, {
            'path': path
        }))

    def build_app(self, host="0.0.0.0"):
        """ Building application means, creation of
        :class:`tornado.web.Application` instance, creation of
        :class:`handler.DynamicHandler` routes, adding routes
        into tornado application, registration of
        :class:`tornado.web.StaticFileHandler`s
        """
        self.app = Application(default_host=host, **self.settings)
        app_ctx = self._build_app_ctx()

        for host, host_definition in self.host_definitions.items():
            handlers = []
            for endpoint, endpoint_definition in host_definition.items():
                handler = self._create_dynamic_handlers(
                        host, endpoint, endpoint_definition, app_ctx)
                handlers.append(*handler[1])
            self.app.add_handlers(host, handlers)

        for url_patttern, static_file_handler_settings \
                in self.static_file_handler_definitions:

            self.app.add_handlers(
                    ".*$",
                    [(url_patttern,
                      StaticFileHandler,
                      static_file_handler_settings)])

        self.is_builded = True

    def _create_dynamic_handlers(self, host, endpoint,
                                 endpoint_definition, app_ctx):
        """ Creates dynamic handler and sets all pipeline functions
        as a dictionary which will be injected to dynamic handler.
        """
        return host, [
                (endpoint,
                 DynamicHandler,
                 dict(
                     endpoint_definition=endpoint_definition,
                     endpoint=endpoint,
                     after_request_funcs=self.after_request_funcs,
                     error_handler_funcs=self.error_handlers,
                     before_request_funcs=self.before_request_funcs,
                     run_in_executor=self.run_in_executor,
                     teardown_request_funcs=self.teardown_request_funcs,
                     app_ctx=app_ctx
                     )
                 )]

    def _build_app_ctx(self):
        """Creates application context object.

        This application context will be used by default
        plugins and will work as a namespace for external uses.

        Rationale behind this approach is that we don't want to clutter
        :class:`handler.DynamicHandler` instances.
        """
        return ApplicationContext()

    def run(self, port=8888, host="0.0.0.0"):
        """Starts an HTTP Server on the given port and host.

        This function also executes :attr:`on_start_funcs` and calls run
        method of :class:`scheduler.Scheduler`
        """
        if not self.is_builded:
            self.build_app(host=host)

        for on_start_func in self.on_start_funcs:
            self.ioloop.run_sync(functools.partial(on_start_func, self))

        self.scheduler.run()
        self.app.listen(port)
        self.ioloop.start()

    def run_in_executor(self, func, *args):
        """runs given function in another thread.
        """
        return futures.wrap_future(self.executor.submit(functools.partial(func, *args)),
                                    loop=self.ioloop.asyncio_loop)

    def add_tornado_handler(self, host_pattern, host_handlers):
        """ To add any handler which extends
        :class:`tornado.web.RequestHandler` class.

        :param host: Hostname to listen to
        :param handlers: list of tuples. Tuples are consist of URL pattern,
                         handler class, handler settings. For more information
                         please check
                         :meth:`tornado.web.Application.add_handlers`
        """
        self.app.add_handlers(host_pattern, host_handlers)


class ApplicationContext(_HandlerBoundObject):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
