from asyncio import get_event_loop
from http import HTTPStatus as status
from uuid import uuid4

from actors import Actor, Opera, rpc
from aiohttp import web

USERS_DATABASE = {}
USERS_STORE_SERVICE = 'core.users:store'
USERS_SERVICE = 'core.users'


def validate(*args, **kwargs):
    '''Adiciona validação dos dados
    '''
    return True


class Store(Actor):
    __service_name__ = USERS_STORE_SERVICE

    @rpc
    async def save(self, request):
        user = request.payload
        user_id = uuid4()
        USERS_DATABASE[user_id] = user
        return request.reply(payload={'id': user_id}, status=status.OK)

    @rpc
    async def get(self, request):
        user_id = request.payload
        try:
            user = USERS_DATABASE[user_id]
        except KeyError:
            return request.reply(None, status.NOT_FOUND)

        user['id'] = user_id
        request.reply(payload=user, status=status.OK)


class Users(Actor):
    __service_name__ = USERS_SERVICE

    @rpc
    async def create(self, request):
        user = request.payload
        if not validate(user):
            return request.reply(status=status.BAD_REQUEST)

        self.request(USERS_STORE_SERVICE, 'save', user)
        return request.reply(status=status.CREATED)

    @rpc
    async def get(self, request):
        return request.reply(status=status.OK)

    @rpc
    async def get_all(self, request):
        return request.reply(status=status.OK)

    @rpc
    async def delete(self, request):
        print('payload:', request.payload)
        return request.reply(status=status.OK)

    @rpc
    async def update(self, request):
        print('payload:', request.payload)
        return request.reply(status=status.ACCEPTED)


loop = get_event_loop()
opera = Opera(loop)
users = Users()
store = Store()

opera.register(users)
opera.register(store)
opera.create_tasks()


async def web_handler(request):
    ret = await opera.request(
        'core.users',
        'get_user', )
    return web.Response(text=ret.payload, status=ret.status)


app = web.Application(loop=loop)
app.router.add_get('/', web_handler)

web.run_app(app)
# loop.run_forever()
