from functools import lru_cache
from asyncio import Queue

from .messages import Request
from .exceptions import ServiceNotFound


class Opera:
    _request_creator = Request

    def __init__(self, loop, lookup_cache_size=1000):
        self.loop = loop
        self.services = {}
        self.get_actor = lru_cache(maxsize=lookup_cache_size)(self._get_actor)
        self.read_queue = Queue(loop=self.loop)
        self.rpc_queue = Queue(loop=self.loop)

    def register(self, actor):
        self.services[actor.channel] = actor
        actor.opera = self

    def create_tasks(self):
        return [
            self.loop.create_task(self._reader()),
            self.loop.create_task(self._rpc_processing()),
        ]

    async def request(self, service, method, payload=None, sender=None):
        request = self._request_creator(
            service=service,
            method=method,
            payload=payload,
            sender=sender,
            loop=self.loop,
        )
        await self.rpc_queue.put(request)

        return await request.awaitable()

    def _get_actor(self, service):
        try:
            return self.services[service]
        except KeyError:
            raise ServiceNotFound

    async def _reader(self):
        while True:
            request = await self.read_queue.get()
            await self.rpc_queue.put(request)

    async def _rpc_processing(self):
        while True:
            request = await self.rpc_queue.get()
            actor = self.get_actor(request.service)
            await actor.receive(request)
