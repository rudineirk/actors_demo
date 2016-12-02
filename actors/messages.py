from asyncio import get_event_loop, CancelledError


class Message:
    __msg_type__ = ''

    def __init__(self, payload=None, sender=None, loop=None):
        self.payload = payload
        self.sender = sender
        self.loop = loop if loop is not None else get_event_loop()

    def create_future(self):
        return self.loop.create_future()


class Reply(Message):
    __msg_type__ = 'reply'

    def __init__(self, status=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = status


class Request(Message):
    __msg_type__ = 'request'
    _reply_creator = Reply

    def __init__(self, service=None, method=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = service
        self.method = method
        self._reply = self.create_future()

    def reply(self, payload=None, status=None, sender=None):
        return self._reply.set_result(self._reply_creator(
            payload=payload,
            status=status,
            sender=sender,
        ))

    async def awaitable(self):
        try:
            await self._reply
            if self._reply.exception():
                ret = self._reply_creator(status=500, loop=self.loop)
            else:
                ret = self._reply.result()
        except CancelledError:
            ret = self._reply_creator(status=500, loop=self.loop)

        return ret
