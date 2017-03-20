import logging
import datetime

from tornado.ioloop import PeriodicCallback, IOLoop

from .errors import ConfigurationError
from .helpers import _HandlerBoundObject


logger = logging.getLogger("flasky.cache")

class CacheManager(object):

    def __init__(self, app):
        self.app = app
        self.ioloop = app.ioloop or IOLoop.currrent()
        self.caches = []
        app.on_start(self.on_start_hook)
        app.before_request(self.before_request_hook)

    def register(self, cache_name=None, interval=None, run_immediate=False):
        if not cache_name:
            raise ConfigurationError('Cant register cache without a name.')

        if not interval:
            raise ConfigurationError('Cant register cache without a interval.')

        def decorator(f):
            self.caches.append(Cache(cache_name, f, interval,
                                     run_immediate=run_immediate,
                                     ioloop=self.ioloop,
                                     app=self.app))
            return f

        return decorator

    def on_start_hook(self, app):
        for cache in self.caches:
            logger.debug("running registered cache<name={}>".format(cache.cache_name))
            cache.run()

    def before_request_hook(self, handler, method_definition):
        if not hasattr(handler, "context"):
            raise ConfigurationError("Context object must be set before this plugin works")

        handler.context.cache = self._build_context()

    def _build_context(self):
        caches = {}
        for cache in self.caches:
            if cache.is_running():
                if hasattr(cache, "data"):
                    caches[cache.cache_name] = cache.data
        return CacheContext(caches)


class CacheContext(_HandlerBoundObject):

    def __init__(self, caches):
        super().__init__(**caches)


class Cache(object):

    def __init__(self, cache_name, cache_func,
                       cache_interval, run_immediate=False,
                       ioloop=None, app=None):
        self.app = app
        self.cache_name = cache_name
        self.cache_func = cache_func
        self.wrapper_cache_func = self._wrap_func(cache_func)

        self.cache_interval = cache_interval
        self.run_immediate = run_immediate
        self.ioloop = ioloop or IOLoop.current()
        self.cb = None

    def _wrap_func(self, f):
        async def wrapper():
            started_at = datetime.datetime.now()
            logging.info("Cache<{}> has been started at <{}>.".format(self.cache_name, started_at))
            data = await f()
            self.data = data
            self.update_stats(data)
            logger.info("Cache<{}> finished lofinished loading data in <{}>"
                    .format(self.cache_name, (datetime.datetime.now() - started_at)))
        return wrapper

    def run(self):
        if self.run_immediate:
            logging.info("Cache<{}> running immediately.".format(self.cache_name))
            self.run_immediately()

        cb = self._create_periodic_callback()
        cb.start()
        self.cb = cb

    def _create_periodic_callback(self):
        return PeriodicCallback(self._wrap_func(self.cache_func), self.cache_interval,
                io_loop=self.ioloop)

    def is_running(self):
        return self.cb.is_running()

    def run_immediately(self):
        self.ioloop.add_callback(self._wrap_func(self.cache_func))

    def stop(self):
        self.cb.stop()

    def update_stats(self, data):
        pass

    def stats(self):
        pass

