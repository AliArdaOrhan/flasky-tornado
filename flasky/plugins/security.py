import jwt

from flasky import errors

REQUIRES_ROLE_KEY = 'requires_role'
BEARER_HEADER = 'Bearer'


def __parse_header(handler, secret):
    authorization_header = handler.request.headers.get('Authorization', None)
    if not authorization_header:
        return

    tokens = authorization_header.split(' ')

    if not tokens[0] == BEARER_HEADER:
        return

    return jwt.decode(tokens[1], secret)


def __is_secure_endpoint(method_definition):
    return True if method_definition.get(REQUIRES_ROLE_KEY, None) else False


def __init_jwt_plugin(app, role_key='roles', **kwargs):

    secret = app.settings.get('secret', None) or kwargs.get('secret', None) or None

    if not secret:
        errors.ConfigurationError('JWT plugin needs secret to work...')

    @app.before_request
    def check_token(handler, method_definition):
        authorization_header = handler.request.headers.get('Authorization', None)
        is_secure_endpoint = __is_secure_endpoint(method_definition)

        if not authorization_header and not is_secure_endpoint:
            #: Not secure endpoint, no authorization header is needed
            setattr(handler, 'token', None)
            return

        if not authorization_header and is_secure_endpoint:
            raise errors.AuthorizationError('User needs jwt token for this endpoint.')

        if not authorization_header.startswith('Bearer'):
            raise errors.AuthorizationError('Token must be a bearer token.')

        try:
            token = jwt.decode(authorization_header.split(' ')[1].decode('utf-8'), key=secret)
            user_role = token.get(role_key, None)
            if not user_role:
                raise errors.InvalidTokenError('Token has no fields with key ' + role_key)

            for required_role in method_definition.get(REQUIRES_ROLE_KEY):
                if required_role == user_role:
                    return

            raise errors.AuthorizationError('User has no privilege to use this endpoint.')

        except jwt.InvalidTokenError as e:
            raise errors.InvalidTokenError(e.args[1])



def init_plugin(app, plugin='JWT',**kwargs):

    if plugin == 'JWT':
        __init_jwt_plugin(app, **kwargs)






