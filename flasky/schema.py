import datetime

from jsonschema import Draft4Validator
from jsonschema import FormatChecker

from flasky.errors import BadRequestError


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