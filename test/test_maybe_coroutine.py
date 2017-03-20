import os
import sys
from asyncio import iscoroutinefunction

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__) + '/../'))
import flasky.helpers


maybe_coroutine = flasky.helpers.maybe_coroutine

@pytest.mark.asyncio
async def test_normal_function_can_be_used_in_io_loop_when_it_is_wrapped_with_maybe_coroutine():
    executed = {"value" : False}
    def sync_function():
        executed["value"] = True

    wrapped_as_coro = maybe_coroutine(sync_function)
    assert iscoroutinefunction(wrapped_as_coro)

    await wrapped_as_coro()
    assert executed["value"]





