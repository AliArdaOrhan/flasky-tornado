import asyncio
import pytest
from flasky.scheduler import Scheduler
from tornado.platform.asyncio import BaseAsyncIOLoop


def test_schedule_should_increment_scheduled_functions_count_by_one():
    scheduler = Scheduler()

    @scheduler.schedule(interval=3000)
    async def scheduled():
        pass

    assert scheduler.jobs_count == 1


def test_run_jobs_should_turn_all_jobs_into_periodic_callbacks(event_loop):
    scheduler = Scheduler(ioloop=BaseAsyncIOLoop(event_loop))

    @scheduler.schedule(interval=3000)
    async def scheduled():
        pass

    assert scheduler.jobs_count == 1
    scheduler.run()

    assert scheduler.running_jobs_count == 1


class JobStub(object):

    def __init__(self):
        self.is_runned = False
        self.run_count = 0

    async def run(self):
        self.is_runned = True
        self.run_count += 1


@pytest.mark.asyncio
async def test_after_run_job_job_should_be_run_for_once(event_loop):
    scheduler = Scheduler(ioloop=BaseAsyncIOLoop(event_loop))
    job = JobStub()

    @scheduler.schedule(interval=3000)
    async def scheduled():
        await job.run()

    scheduler.run()

    await asyncio.sleep(1)

    assert job.is_runned
    assert job.run_count == 1


@pytest.mark.asyncio
async def test_run_should_run_function_2_times_in_3_sec(event_loop):
    #: First run(will be triggered at run) and scheduled second run.
    scheduler = Scheduler(ioloop=BaseAsyncIOLoop(event_loop))
    job = JobStub()

    @scheduler.schedule(interval=2000)
    async def scheduled():
        await job.run()

    scheduler.run()

    await asyncio.sleep(3)

    assert job.is_runned
    assert job.run_count == 2


@pytest.mark.asyncio
async def test_stop_should_decrease_running_job_count(event_loop):
    scheduler = Scheduler(ioloop=BaseAsyncIOLoop(event_loop))

    @scheduler.schedule(interval=3000, name="test")
    async def test_job():
        pass

    scheduler.run()
    assert scheduler.running_jobs_count == 1
    asyncio.sleep(1)
    scheduler.stop_all()
    assert scheduler.running_jobs_count == 0
