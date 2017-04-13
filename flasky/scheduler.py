from collections import OrderedDict
from tornado.ioloop import PeriodicCallback, IOLoop


class Scheduler(object):

    def __init__(self, ioloop=None):
        self.ioloop = ioloop or IOLoop.current()
        self.job_definitions = []
        self.running_jobs = OrderedDict()

    @property
    def jobs_count(self):
        return len(self.job_definitions)

    @property
    def running_jobs_count(self):
        return len(self.running_jobs)

    def schedule(self, name=None, interval=None):
        def wrapper(f):
            job_name = name if name else f.__name__

            self.job_definitions.append(
                    {
                        "func": f,
                        "interval": interval,
                        "name": job_name
                     })
            return f
        return wrapper

    def stop(self, job_name):
        job = self.running_jobs.pop(job_name, None)
        if not job:
            raise ValueError("Job is not found with given key")
        job.stop()

    def stop_all(self):
        for name, running_job in self.running_jobs.items():
            running_job.stop()

        self.running_jobs = OrderedDict()

    def run(self):
        for job_definition in self.job_definitions:
            func = job_definition["func"]
            interval = job_definition["interval"]

            job = build_job(func, interval, self.ioloop)
            job.start()

            self.running_jobs[job_definition["name"]] = job
            self.ioloop.add_callback(func)


def build_job(func, interval, ioloop):
    """This function primary purpose is present a single point
    for creating job that specific to event loop. Currently,
    only supported job type is tornado's
    :class:`~tornado.ioloop.PeriodicCallback`
    """
    return PeriodicCallback(func, interval, io_loop=ioloop)
