## Quark-Flasky
Tornado uygulamaları için Thin-Wrapper.


#### Quickstart
Minimal application of Quark-Flasky looks something like this:

```python
from flasky import FlaskyApp
app = FlaskyApp()

@app.api(
    endpoint='/login',
    method= 'GET'
)
async def hello_world(handler):
    handler.write('Hello world')

if __name__ == '__main__':
    app.run(8888)
```

Quark-Flasky applications are programmed via set of decorators.



```python

'''app.ap is register functions which is used to define endpoint. DynamicHandler, positional and named arguments are passed in when endpoint is executed.

 Parameters:
    host: Virtual host parameter which takes in regex as the first argument.
          Default value: .*$
    endpoint: Regular expression to be matched for urls. Must conform tornado.web.URLSpec
    standards.
    method: HTTP Method of given endpoint. Can be ['POST','PUT', 'GET', 'DELETE', 'PATCH', 'HEAD']
'''


@app.api(
    endpoint='/login',
    method= 'GET'
)
async def hello_world(handler, *args, **kwargs):
    handler.write('Hello world')
```



```python
'''``app.before_request`` register functions which is executed before a request passed to handler. For many extensions this is the configuration point.
'''

@app.before_request
async def check_authorization_header(handler, method_definition, *args, **kwargs):
    is_secure = method_definition.get('is_secure', None)
    if not is_secure:
        return
    if not handler.request.headers.get('Authorization', None):
        raise AuthorizationError()
```

```python
'''``app.after_request`` register functions which is ALWAYS executed after a request passed to handler. This can be configuration point for many plugins.
'''

@app.after_request
async def add_cors_headers(handler, *args, **kwargs):
    handler.set_header('Access-Control-Allow-Origin', '*')
    handler.set_header('Access-Control-Allow-Methods', '*')
```

```python

'''``app.error_handler`` register functions which is executed when a exception occurs during execution of handler chain

Parameters:
    exc_type: Exception type that will be handled. Default is None which means handler
              executed for all type of errors
'''

@app.error_handler
async def default_error_handler(handler, err):
    await kafka_producer.send('error_queue', 'Error message: {}'.format(str(err)))

@app.error_handler(MyBaseExceptionClass)
async def my_exception_handler(handler, err):
    await handler.write({
        'Status': err.status_code,
        'Message': err.message
    })
    logger.error(err)
```


```python
'''``app.after_request`` is decorator which is ALWAYS executed after a request passed to handler. This can be configuration point for many plugins.
'''

@app.after_request
async def add_cors_headers(handler, *args, **kwargs):
    handler.set_header('Access-Control-Allow-Origin', '*')
    handler.set_header('Access-Control-Allow-Methods', '*')
```












