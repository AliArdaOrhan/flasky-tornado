import datetime

from jsonschema import Draft4Validator
from jsonschema import FormatChecker

from flasky import BadRequestError


def validate_schema(schema, data):
    validator = Draft4Validator(
        schema,
        types={"datetime": datetime.datetime},
        format_checker=FormatChecker())

    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        print(errors)
        raise BadRequestError(message="ERRORS.VALIDATION_ERROR")