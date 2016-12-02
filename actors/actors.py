from functools import lru_cache

from .exceptions import MethodNotFound


def export_rpc(func):
    func._rpc_exported = True
    return func


def rpc(*args):
    _rpc_registered_name = None

    def _make_actor_method(func):
        if _rpc_registered_name is None:
            func._rpc_registered_name = func.__name__
        else:
            func._rpc_registered_name = func.__name__

        return func

    if len(args) == 1 and callable(args[0]):
        return _make_actor_method(args[0])
    else:
        _rpc_registered_name = args[0]
        return _make_actor_method


class ActorMeta(type):
    def __new__(cls, name, bases, attrs):
        attrs = cls.register_rpc(attrs)
        return super().__new__(cls, name, bases, attrs)

    def register_rpc(attrs):
        _rpc_methods = {}
        for method in attrs.values():
            if callable(method) and hasattr(method, '_rpc_registered_name'):
                _rpc_methods[method._rpc_registered_name] = method

        attrs['_rpc_methods'] = _rpc_methods
        return attrs


class Actor(metaclass=ActorMeta):
    _rpc_methods = {}
    __service_name__ = ''

    def __init__(self, opera=None, lookup_cache_size=100):
        self.opera = opera
        self.get_rpc_method = lru_cache(
            maxsize=lookup_cache_size,
        )(self._get_rpc_method)

    async def receive(self, msg):
        if msg.__msg_type__ == 'request':
            return await self.get_rpc_method(msg.method)(self, msg)

    async def request(self, *args, **kwargs):
        return self.opera.request(*args, **kwargs)

    @property
    def channel(self):
        return self.__service_name__

    def _get_rpc_method(self, method):
        try:
            return self._rpc_methods[method]
        except KeyError:
            raise MethodNotFound
