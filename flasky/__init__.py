
print('LOADING FLASK')

class FlaskyTornError(BaseException):

    def __init__(self, status_code=None, message=None):
        self.status_code = status_code
        self.message = message


class ConfigurationError(FlaskyTornError):

    def __init__(self, message=None):
        super().__init__(status_code=500, message=message)

    def __str__(self):
        return self.message

class BadRequestError(FlaskyTornError):

    def __init__(self, message=None):
        super().__init__(status_code=400, message=message)


class InvalidTokenError(FlaskyTornError):

    def __init__(self, message=None):
        super().__init__(status_code=403, message=message)


class TokenBlacklistedError(FlaskyTornError):

    def __init__(self):
        super().__init__(status_code=403, message='Token is already blacklisted...')

class MethodIsNotAllowed(FlaskyTornError):

    def __init__(self):
        super().__init__(status_code=405, message='Method is not allowed.')