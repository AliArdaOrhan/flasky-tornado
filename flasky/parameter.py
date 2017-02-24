import json

from flasky.errors import BadRequestError


class JSONParam(object):

    def __init__(self, param_name=None, param_path=None, is_required=False):
        self.param_name = param_name
        self.param_path = param_path
        self.is_required = is_required
        self.param_levels = []
        if '.' in param_path:
            self.param_levels = param_path.split('.')
        else:
            self.param_levels.append(param_path)

    def resolve(self, body):
        val = body
        for param_level in self.param_levels:
            val = val.get(param_level, None)
            if not val:
                break
        return val


class QueryParam(object):

    def __init__(self, parameter_name, parameter_type):
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type



class JSONParameterResolver(object):
    def __init__(self, parameter_path):
        self.parameter_path = parameter_path
        self.param_levels = []
        if '.' in parameter_path:
            self.param_levels = parameter_path.split('.')
        else:
            self.param_levels.append(parameter_path)

    def resolve(self, handler):
        try:
            as_json = json.loads(handler.request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise BadRequestError('This method needs JSON body request.')

        val = as_json
        for param_level in self.param_levels:
            val = val.get(param_level, None)
            if not val:
                break
        return val


