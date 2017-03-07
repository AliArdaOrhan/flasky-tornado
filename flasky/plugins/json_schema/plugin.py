import datetime

from jsonschema import Draft4Validator
from jsonschema import FormatChecker

from flasky.errors import BadRequestError

class JsonSchemaPlugin(object):

    def __init__(self, app):
        self.app = app

        self.init_app(app)

    def init_app(self, app):
        app.before_request(self.__validate_schema)


    def __validate_schema(self, request_context, method_definition):
        schema = method_definition.get('json_schema', None)
        if not schema:
            return

        validate_schema(schema, request_context.body_as_json)


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