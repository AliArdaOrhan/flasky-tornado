import json
import logging

logger = logging.getLogger("flasky.errors")

class FlaskyTornError(BaseException):

    def __init__(self, status_code=None, message=None, reason=None):
        self.status_code = status_code
        self.message = message
        self.reason = reason

class ResourceNotFoundError(FlaskyTornError):

    def __init__(self, message='Resource not found', reason=None):
        super().__init__(status_code=404, message=message, reason=reason)

class ResourceAlreadyExistsError(FlaskyTornError):

    def __init__(self, message="Resource is already exists.", reason=None):
        super().__init__(status_code=409, message=message, reason=reason)

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
        super().__init__(status_code=403, message='Token is already blacklisted...')

class MethodIsNotAllowed(FlaskyTornError):

    def __init__(self):
        super().__init__(status_code=405, message='Method is not allowed.')

class AuthorizationError(FlaskyTornError):

    def __init__(self, message, reason=None):
        super().__init__(status_code=403, message=message, reason=reason)

async def default_error_handler_func(handler, err):

    if isinstance(err, FlaskyTornError):
        logger.exception(err.message)
        handler.clear()
        handler.write(json.dumps({
            'status': err.status_code,
            'message': err.message
        }))
        handler.set_status(err.status_code)
        return
    raise err