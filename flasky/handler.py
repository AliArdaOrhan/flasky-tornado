import json

import tornado.web

from concurrent.futures import ThreadPoolExecutor

from flasky.errors import BadRequestError, MethodIsNotAllowed

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
        try:
            await self._do_handle(method, *args, **kwargs)
        except BaseException as e:
            error_handler = self.error_handler_funcs[type(e)] if type(e) in self.error_handler_funcs else self.error_handler_funcs[None]
            await error_handler(self, e)

        for after_request_func in self.after_request_funcs:
            await after_request_func(self)

    def _get_method_definition(self, method_name):
        return self.endpoint_definition.get(method_name, None)

    async def _do_handle(self, method, *args, **kwargs):
        method_definition = self._get_method_definition(method)

        if self.user_loader_func:
            self.user = await self.user_loader_func(self)

        for before_request_func in self.before_request_funcs:
            await before_request_func(self, method_definition)

        #: Check if method exists?
        handler_function = method_definition.get('function', None)
        if not handler_function:
            raise MethodIsNotAllowed()

        #: Apply Schema Validator
        schema_validator = method_definition.get('json_schema', None)
        if schema_validator:
            self.load_body_as_json()
            schema_validator(self.body_as_json)

        #: Resolve parameters
        params = self._resolve_parameters(method_definition['parameters'])
        if params:
            kwargs.update({'params': params})

        #: Do actual execution
        await handler_function(self, *args, **kwargs)




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

    def load_body_as_json(self):
        try:
            self.body_as_json = json.loads(self.request.body.decode('utf-8'))
        except json.JSONDecodeError:
            raise BadRequestError('Body should be json object.')




