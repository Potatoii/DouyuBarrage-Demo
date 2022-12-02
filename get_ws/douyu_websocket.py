import asyncio
import re
import time

from aiowebsocket.converses import Converse

import settings

from commons.log_utils import logger


class DouyuWebSocket:
    def __init__(self):
        self.room_id = settings.ROOM_ID

    async def login_msg(self):
        """
        发送登录请求消息
        """
        msg = f"type@=loginreq/roomid@={self.room_id}/"
        msg_bytes = await self.dy_encode(msg)
        return msg_bytes

    async def group_msg(self):
        """发送入组消息"""
        msg = f"type@=joingroup/rid@={self.room_id}/gid@=-9999/"
        msg_bytes = await self.dy_encode(msg)
        return msg_bytes

    async def keeplive(self, converse: Converse) -> None:
        while True:
            """
            保持心跳
            """
            msg = f"type@=keeplive/tick@={str(int(time.time()))}/\0"
            beat_msg = await self.dy_encode(msg)
            await converse.send(beat_msg)
            await asyncio.sleep(15)

    async def on_message(self, message: bytes) -> dict:
        """
        将字节流转化为字符串，忽略无法解码的错误（即斗鱼协议中的头部尾部）
        """
        msg = message.decode(encoding="utf-8", errors="ignore")
        if re.search(r"type@=(.*?)/", msg):
            msg_type = re.search(r"type@=(.*?)/", msg).group(1)
            if msg_type == "chatmsg":
                barrage_dict = await self.format_barrage_dict(msg)
                return barrage_dict
        elif re.search(r"@AA", msg):
            return {}
        else:
            logger.error(f"奇怪的msg:{msg}")

    @classmethod
    async def dy_encode(cls, msg: str) -> bytes:
        """
        编码
        """
        # 头部8字节，尾部1字节，与字符串长度相加即数据长度
        data_len = len(msg) + 9
        # 字符串转化为字节流
        msg_byte = msg.encode("utf-8")
        # 将数据长度转化为小端整数字节流
        len_byte = int.to_bytes(data_len, 4, "little")
        # 前两个字节按照小端顺序拼接为0x02b1，转化为十进制即689（《协议》中规定的客户端发送消息类型）
        # 后两个字节即《协议》中规定的加密字段与保留字段，置0
        send_byte = bytearray([0xb1, 0x02, 0x00, 0x00])
        # 尾部以"\0"结束
        end_byte = bytearray([0x00])
        # 按顺序拼接在一起
        data = len_byte + len_byte + send_byte + msg_byte + end_byte
        return data

    @classmethod
    async def format_barrage_dict(cls, msg: str) -> dict:
        try:
            barrage_dict = dict(
                rid=int(re.search(r"rid@=(.*?)/", msg).group(1)),  # 房间号
                uid=int(re.search(r"uid@=(.*?)/", msg).group(1)),  # 用户id
                nickname=re.search(r"nn@=(.*?)/", msg).group(1),  # 用户昵称
                level=int(re.search(r"level@=(.*?)/", msg).group(1)),  # 用户等级
                bnn=re.search(r"bnn@=(.*?)/", msg).group(1),  # 粉丝牌名称
                bnn_level=int(re.search(r"bl@=(.*?)/", msg).group(1)),  # 粉丝牌等级
                brid=int(re.search(r"brid@=(.*?)/", msg).group(1)),  # 粉丝牌房间号
                is_diaf=int(re.search(r"diaf@=(.*?)/", msg).group(1)) if "diaf@=" in msg else 0,  # 是否是钻石粉丝
                content=re.search(r"txt@=(.*?)/", msg).group(1)  # 弹幕内容
            )
            return barrage_dict
        except:  # noqa
            logger.error(f"奇怪的msg:{msg}")
            return {}
