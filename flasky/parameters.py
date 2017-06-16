import json

from flasky.errors import FlaskyTornError, ConfigurationError
from .helpers import _HandlerBoundObject


class ParameterRequiredError(FlaskyTornError):

    def __init__(self, message):
        super().__init__(status_code=400, message=message)


class ParameterResolver(object):

    def __init__(self, app):
        self.app = app
        app.before_request(self.bind_params)

    def bind_params(self, handler, method_definition):
        parameter_definitions = method_definition.get('params', [])

        if not isinstance(parameter_definitions, (list, set)):
            parameter_definitions = set(parameter_definitions)

        parameter_map = {}
        for parameter_definition in parameter_definitions:
            parameter_map[parameter_definition.parameter_name] = parameter_definition.resolve(handler)

        if not hasattr(handler, "context"):
            raise ConfigurationError("Handler object should have context field \
                    set before any other plugin work")

        setattr(handler.context, "parameters",
                _HandlerBoundObject(**parameter_map))


class ResolvableParameter(object):

    def __init__(self, parameter_name, is_required=False,
                 default=None, typ=str):
        if parameter_name is None:
            raise ConfigurationError('Parameter name must not be None...')

        if typ not in {str, bool, float, int, list, set, callable}:
            raise ConfigurationError(
                    "Parameter<{}> type must be in bool, str, int, float"
                    .format(parameter_name))

        self.parameter_name = parameter_name
        self.is_required = is_required
        self.default = default
        self.typ = typ

    def resolve(self, handler):
        val = self.do_resolve(handler)

        if val is not None:
            return self.typ(val)

        if self.is_required:
            raise ParameterRequiredError(
                    "Parameter-{}- is required but not exists."
                    .format(self.parameter_name))

        return None

    def do_resolve(self, handler):
        raise NotImplemented


class QueryParameter(ResolvableParameter):

    def __init__(self, parameter_name, is_required=False,
                 default=None, typ=str):
        super().__init__(parameter_name, is_required=is_required,
                         default=default, typ=typ)

    def do_resolve(self, handler):
        return handler.get_query_argument(self.parameter_name,
                                          default=self.default)


class CollectionQueryParameter(ResolvableParameter):

    def __init__(self, parameter_name, is_required=False,
                 default=None, mapper=None):

        super().__init__(parameter_name, is_required, default, typ=list)
        self.mapper = mapper

    def do_resolve(self, handler):
        vals = handler.get_arguments(self.parameter_name, strip=True)

        if len(vals) > 0:
            return vals if not self.mapper else [self.mapper(val) for val in vals]

        return self.default if self.default else None

class BodyArgument(ResolvableParameter):

    def __init__(self, parameter_name, is_required=False, default=None, typ=str):
        super().__init__(parameter_name, is_required, default, typ)

    def do_resolve(self, handler):
        return handler.get_body_argument(self.parameter_name, default=None, strip=True)


class CollectionBodyArgument(ResolvableParameter):

    def __init__(self, parameter_name, is_required=False, default=None, mapper=None):
        super().__init__(parameter_name, is_required, default, list)
        self.mapper = mapper

    def do_resolve(self, handler):
        vals = handler.get_body_arguments(self.parameter_name)

        if len(vals) == 0:
            return self.default

        if self.mapper:
            return [self.mapper(val) for val in vals]

        return vals


class JSONPathArgument(object):

    def __init__(self, parameter_name, path=None, is_required=False, default=None, mapper=None):
        self.parameter_name = parameter_name
        self.is_required = is_required
        self.default = default
        self.parameter_path = path
        self.mapper = mapper
        
        if self.parameter_path and  "." in self.parameter_path:
            self.splitted = [
                                path
                                for path in self.parameter_path.split(".")
                                if path.strip() != ""
                            ]
        elif self.parameter_path is not None:
            self.splitted = [self.parameter_path]
        
    def resolve(self, handler):
        body = self._get_json(handler)
        if not body:
            return self._handle_none_body()
        
        if not self.parameter_path:
            return body

        val = body
        for key in self.splitted:
            if key not in val:
                if self.default:
                    return self.default
                if self.is_required:
                    raise ParameterRequiredError("Parameter<{}> is required but not found."
                            .format(self.parameter_name))
                return None
            val = val[key]

        return self.mapper(val) if self.mapper else val


    def _handle_none_body(self):
        if self.default is not None:
            return self.default

        if not self.is_required:
            return None

        raise ParameterRequiredError("JsonBody parameter<path={}> is required but body was none."
                    .format(self.parameter_path))



    def _get_json(self, handler):
        try:
            body = handler.body_as_json(throw_exc=True)
            return handler.body_as_json()
        except json.JSONDecodeError:
            return None





