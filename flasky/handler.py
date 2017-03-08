import json
from asyncio import iscoroutinefunction
from json import JSONDecodeError

import tornado.web

from concurrent.futures import ThreadPoolExecutor

from flasky.errors import BadRequestError, MethodIsNotAllowed

from flasky.util import maybe_future


# noinspection PyAttributeOutsideInit,PyAbstractClass
class DynamicHandler(tornado.web.RequestHandler):

    executor_pool = ThreadPoolExecutor()

    def initialize(self, endpoint=None, endpoint_definition=None,
                   after_request_funcs=None, before_request_funcs=None, user_loader_func=None,
                   error_handler_funcs=None, run_in_executor=None, teardown_request_funcs = None):

        #: Flasky app.
        self.run_in_executor = run_in_executor

        #: A dictionary all handlers will be registered. Keys will be method of handler.
        self.endpoint_definition = endpoint_definition

        #: Endpoint of this handler for logging purposes
        self.endpoint = endpoint

        #: List of functions will be executed after request is handled.
        self.after_request_funcs = after_request_funcs or []

        self.before_request_funcs = before_request_funcs or []

        self.error_handler_funcs = error_handler_funcs or []

        self.teardown_request_funcs = teardown_request_funcs or []

        self.user_loader_func = user_loader_func

        self.user = None

        self.body_as_json = None

    async def post(self, *args, **kwargs):
        await self._handle('POST', *args, **kwargs)

    async def get(self, *args, **kwargs):
        await self._handle('GET', *args, **kwargs)

    async def patch(self, *args, **kwargs):
        await self._handle('PATCH', *args, **kwargs)

    async def put(self, *args, **kwargs):
        await self._handle('PUT', *args, **kwargs)

    async def options(self, *args, **kwargs):
        await self._handle('OPTIONS', *args, **kwargs)

    async def head(self, *args, **kwargs):
        await self._handle('HEAD', *args, **kwargs)

    async def delete(self, *args, **kwargs):
        await self._handle('DELETE', *args, **kwargs)

    async def _handle(self, method, *args, **kwargs):
        request_context = RequestContext(self)
        request_context.add_args(*args)
        request_context.add_kwargs(**kwargs)

        method_definition = self._get_method_definition(method)

        try:
            await self._do_handle(method_definition, request_context)
        except BaseException as e:
            error_handler = self.error_handler_funcs[type(e)] if type(e) in self.error_handler_funcs else self.error_handler_funcs[None]
            await error_handler(self, e)

    def _get_method_definition(self, method_name):
        return self.endpoint_definition.get(method_name, None)

    async def _do_handle(self, method_definition, request_context):
        if self.user_loader_func:
            self.user = await self.user_loader_func(request_context, method_definition)

        handler_function = method_definition.get('function', None)
        if not handler_function:
            raise MethodIsNotAllowed()

        for before_request_func in self.before_request_funcs:
            if iscoroutinefunction(before_request_func):
                await before_request_func(request_context, method_definition)
            else:
                before_request_func(request_context, method_definition)


        await handler_function(request_context.handler, *request_context.args, **request_context.kwargs)

        for after_request_func in self.after_request_funcs:
            await after_request_func(request_context, method_definition)

    def _resolve_parameters(self, parameter_definitions):
        if not parameter_definitions:
            return

        if not len(parameter_definitions) > 0:
            return

        parameter_values = {}
        for parameter_definition in parameter_definitions:
            val = parameter_definition.resolve(self.body_as_json)
            if not val and parameter_definition.is_required:
                raise BadRequestError('Parameter {} is required...'.format(parameter_definition.param_path))
            parameter_values[parameter_definition.param_name] = val

        return parameter_values


class RequestContext(object):

    def __init__(self, handler):
        self.handler = handler
        self._body = self.handler.request.body
        self._body_as_json = None
        self._context_vars = {}
        self._extra_args = []
        self._extra_kwargs = {}

    @property
    def args(self):
        return self._extra_args

    @property
    def kwargs(self):
        return self._extra_kwargs

    def get(self, key, default=None):
        return self._context_vars.get(key, default)

    def put(self, key, value):
        self._context_vars[key] = value

    @property
    def headers(self):
        return self.handler.request.headers

    @property
    def request(self):
        return self.handler.request

    @property
    def body(self):
        return self._body

    @property
    def body_as_json(self, **kwargs):
        if not self._body_as_json:
            try:
                self._body_as_json = json.loads(self._body.decode('utf-8'), **kwargs)
            except json.JSONDecodeError as e:
                raise BadRequestError('Error while decoding json. msg={}'.format(e.args[0]))

        return self._body_as_json

    def add_kwargs(self, **extra_kwargs):
        self._extra_kwargs.update(extra_kwargs)

    def add_args(self, *args):
        self._extra_args.extend(args)





