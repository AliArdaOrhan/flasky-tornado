from asyncio import Future


def maybe_future(result):
    if isinstance(result, Future):
        return result

    f = Future()
    f.set_result(result)
    return f