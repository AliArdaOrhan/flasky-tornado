import decimal
import datetime
from bson import ObjectId
from bson.json_util import default
from asyncio import iscoroutinefunction


class _HandlerBoundObject(object):
    """ Purpose of this object is to programatticaly
    configure return value of property accesses
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getattr__(self, item):
        try:
            object.__getattribute__(self, item)
        except AttributeError:
            return None


def maybe_coroutine(f):
    if iscoroutinefunction(f):
        return f

    async def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


#: TODO delete these functions
def object_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = datetime.datetime.strptime(
                value, "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            pass
    return json_dict


def bson_to_json(o):
    if isinstance(o, (ObjectId, decimal.Decimal)):
        return str(o)
    elif isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
        r = o.isoformat()
        if isinstance(o, datetime.time):
            return r[:12]
        elif isinstance(o, datetime.datetime):
            return r + 'Z'
        return r
    return default(o)
