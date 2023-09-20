import asyncio
import threading

from aiowebsocket.converses import AioWebSocket

from commons.log_utils import logger
from douyu_websocket import DouyuWebSocket
from settings import PROXY_URL


def start_handler_loop(start_loop):
    asyncio.set_event_loop(start_loop)
    start_loop.run_forever()


async def init_aiows():
    aiows = AioWebSocket(PROXY_URL)
    create = asyncio.wait_for(aiows.create_connection(), timeout=aiows.timeout)
    try:
        await create
    except asyncio.TimeoutError as exc:
        raise ConnectionError("Connection time out,exc:{exc}".format(exc=exc))
    return aiows


async def startup():
    aiows = await init_aiows()
    converse = aiows.manipulator
    logger.info("#####-正在连接弹幕服务器-#####")
    douyu_websocket = DouyuWebSocket()
    login = await douyu_websocket.login_msg()
    await converse.send(login)
    group = await douyu_websocket.group_msg()
    await converse.send(group)
    logger.info("#####-成功连接弹幕服务器-#####")
    asyncio.run_coroutine_threadsafe(douyu_websocket.keeplive(converse), beat_loop)  # 保持心跳
    while True:
        receive = await converse.receive()
        await douyu_websocket.on_message(receive)


if __name__ == "__main__":
    try:
        logger.info("#####-启动程序-#####")
        loop = asyncio.get_event_loop()

        # 起一个线程用来发送心跳
        beat_loop = asyncio.new_event_loop()
        beat = threading.Thread(target=start_handler_loop, args=(beat_loop,))
        beat.start()

        loop.run_until_complete(startup())
    except KeyboardInterrupt:
        logger.info("退出监控")
