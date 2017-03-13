from flasky import FlaskyTornError, ConfigurationError
from tornado.web import RequestHandler

class ParameterRequiredError(FlaskyTornError):
    def __init__(self, parameter_name):
        super().__init__(status_code=400, message='Parameter{} is required'.format(parameter_name))

class ParameterPlugin(object):

    def __init__(self, app):
        self.app = app
        self.init_app(app)

    def init_app(self, app):
        app.before_request(self.__resolve_parameters)

    def __resolve_parameters(self, request_context, method_definition):
        params = method_definition.get('params', None)
        if not params:
            return

        if not isinstance(params, (list,set)):
            params = set(params)

        extra_kwargs = {}
        for param in params:
            parameter_value = param.resolve(request_context)
            extra_kwargs[param.parameter_name] = parameter_value

        request_context.add_kwargs(**extra_kwargs)


class QueryParam(object):

    def __init__(self, parameter_name, is_required=False, default=None, typ=str):
        if not parameter_name:
            raise ConfigurationError('Parameter name can not be None')

        self.parameter_name = parameter_name
        self.is_required = is_required
        if not typ in [str, bool, float, int]:
            raise ConfigurationError(message='Parameter<{}> type must be in bool, str, int, float.'.format(parameter_name))
        self.typ = typ
        self.default = default

    def resolve(self, request_context):
        handler = request_context.handler
        val = self.typ(handler.get_query_argument(self.parameter_name, default=self.default))

        if self.is_required and not val:
            raise ParameterRequiredError(self.parameter_name)

        if not val and self.default:
            return self.default

        return val
