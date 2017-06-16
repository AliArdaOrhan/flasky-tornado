import json
import logging

logger = logging.getLogger("flasky.errors")


class FlaskyTornError(BaseException):

    def __init__(self, status_code=None, err_code=None, message=None, reason=None):
        self.status_code = status_code
        self.err_code = err_code or "errors.InternalError"
        self.message = message
        self.reason = reason


class ResourceNotFoundError(FlaskyTornError):

    def __init__(self, message='Resource not found', reason=None, err_code="errors.resourceNotFound"):
        super().__init__(status_code=404,
                         message=message,
                         reason=reason,
                         err_code=err_code)


class ResourceAlreadyExistsError(FlaskyTornError):

    def __init__(self, message="Resource is already exists.", err_code="errors.resourceAlreadyExists",
                 collection=None, key=None):
        super().__init__(status_code=409, message=message, reason=reason, err_code=err_code)
        self.collection = collection
        self.key = key


class ConfigurationError(FlaskyTornError):

    def __init__(self, message=None, reason=None):
        super().__init__(status_code=500, message=message, reason=reason)

    def __str__(self):
        return self.message


class BadRequestError(FlaskyTornError):

    def __init__(self, message=None, reason=None):
        super().__init__(status_code=400, message=message, reason=reason)


class InvalidTokenError(FlaskyTornError):

    def __init__(self, message=None, reason=None):
        super().__init__(status_code=403, message=message, reason=reason)


class TokenBlacklistedError(FlaskyTornError):

    def __init__(self):
        super().__init__(
                status_code=403,
                message='Token is already blacklisted...')


class MethodIsNotAllowed(FlaskyTornError):

    def __init__(self):
        super().__init__(status_code=405, message='Method is not allowed.')


class AuthorizationError(FlaskyTornError):

    def __init__(self, message, reason=None):
        super().__init__(status_code=403, message=message, reason=reason)


class ParameterIsRequiredError(FlaskyTornError):
    def __init__(self, required_parameter=None, service_name=None):
        super().__init__(status_code=400, message="Parameter is required for"
                         "this action".format(
                             required_parameter, service_name))


async def default_error_handler_func(handler, err, definition):
    if isinstance(err, FlaskyTornError):
        logger.exception(err.message)
        handler.clear()
        handler.write(json.dumps({
            "error": {
                'status': err.status_code,
                'message': err.message,
                'code': err.err_code
            }
        }))
        handler.set_status(err.status_code)
        handler.set_header("Content-Type", "application/json")
        return
    raise err
