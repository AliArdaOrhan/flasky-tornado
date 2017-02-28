## Introduction To Quark-Flasky
Thin wrapper around Tornado-Web applications for microservice applications.
### Why A New Framework?

[Tornado](https://github.com/tornadoweb/tornado) is a great library for creating web applications. If you do it well, tornado applications has a wonderful performance characteristics. Yet, due to its low-level nature, Most of work, especially cross-cutting concerns, must be done by developers which means a lot efforts and might be resulted in boilerplate code.

Furthermore, with the new hype around microservices, we decided to build our new project with microservice architecture. It's a wild area with new problems that monolithic architectures doesn't have. One of those problems is, _sharing libraries_ between microservices. Shared libraries might include authentication, authorization, logging, monitoring, third-party clients etc. With sharing a library that solves problems above, you can focus on solving business problems instead of drowning in technical challenges.

[Flask](http://flask.pocoo.org/)  is beloved micro-framework in our python community. From its initial release, it becomes one of the most popular web framework in python landspace in relatively short timespan. It powers comes from its simplicity (when you compared to django). Its unopinated, extensible by hooks and has a fairly good ecosystem.

So...

We decided to build a **Thin Wrapper** around Tornado Framework that provide us Flask programming model to implement our shared libraries in a **plugin fashion** across different microservice. And here is Quark-Flasky.

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

'''app.ap is decorator which is used to define endpoint. DynamicHandler, positional and named arguments are passed in when endpoint is executed.

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
'''``app.before_request`` is decorator which is executed before a request passed to handler. For many extensions this is the configuration point.
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
'''``app.after_request`` is decorator which is ALWAYS executed after a request passed to handler. This can be configuration point for many plugins.
'''

@app.after_request
async def add_cors_headers(handler, *args, **kwargs):
    handler.set_header('Access-Control-Allow-Origin', '*')
    handler.set_header('Access-Control-Allow-Methods', '*')
```

 ```python
'''``app.error_handler`` is decorator which is executed when a exception occurs during execution of handler chain

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





@app.api
api decorator is creates the core of framework. Its purpose is to create endpoints
for your application and brings extension points for another plugins. Any URL parameter will be
passed as argument to handler function.

host - default to .$*
endpoint - endpoint url (It can be used for other extensions to provide meta-data for endpoint)
method - HTTP method of Endpoint

@app.before_request
Before request hook is executed before every request. User can implement cross-cutting concerns here.

@app.after_request
After request is executed after every request. User can implement cross-cutting concerns here like CORS headers.

@app.error_handler
Hook that will be executed after an exception thrown

@app.before_request
async def check_auth_header(handler):
  ..authorization logic








 