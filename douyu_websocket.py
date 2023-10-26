import asyncio
import re
import time
from typing import Dict

import settings
from commons.log_utils import logger


class DouyuWebSocket:
    def __init__(self, gifts: Dict):
        self.room_id = settings.ROOM_ID
        self.gifts = gifts

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

    async def keeplive(self, websocket) -> None:
        while True:
            """
            保持心跳
            """
            msg = f"type@=keeplive/tick@={str(int(time.time()))}/\0"
            beat_msg = await self.dy_encode(msg)
            await websocket.send(beat_msg)
            logger.debug("发送心跳")
            await asyncio.sleep(15)

    async def on_message(self, message: bytes):
        """
        将字节流转化为字符串，忽略无法解码的错误（即斗鱼协议中的头部尾部）
        """
        msg = message.decode(encoding="utf-8", errors="ignore")
        logger.debug(f"收到消息:{msg}")
        if re.search(r"@AA", msg):
            return {}
        elif re.search(r"type@=(.*?)/", msg):
            msg_type = re.search(r"type@=(.*?)/", msg).group(1)
            uid_re = re.search(r"uid@=(.*?)/", msg)
            if uid_re:
                uid = int(uid_re.group(1))
                if uid in settings.EYEFUCK_ID_LIST:
                    if msg_type == "uenter":
                        nickname = re.search(r"nn@=(.*?)/", msg).group(1)
                        level = int(re.search(r"level@=(.*?)/", msg).group(1))
                        logger.info(f"[Lv{level}] {nickname} 进入了直播间")
                    elif msg_type == "chatmsg":
                        chatmsg_dict = await self.format_chatmsg_dict(msg)
                        if chatmsg_dict.get("bnn"):
                            logger.info(
                                f"[Lv{chatmsg_dict.get('level')}]【{chatmsg_dict.get('bnn')}】{chatmsg_dict.get('nickname')}:{chatmsg_dict.get('content')}")
                        else:
                            logger.info(
                                f"[Lv{chatmsg_dict.get('level')}]{chatmsg_dict.get('nickname')}:{chatmsg_dict.get('content')}")
                    elif msg_type == "dgb":
                        try:
                            gift_id_list = re.findall(r"gfid@=(.*?)/", msg)
                            gift_count_list = re.findall(r"gfcnt@=(.*?)/", msg)
                            for gift_id, gift_count in zip(gift_id_list, gift_count_list):
                                nickname = re.search(r"nn@=(.*?)/", msg).group(1)
                                level = int(re.search(r"level@=(.*?)/", msg).group(1))
                                gift_name = self.gifts[gift_id]["name"]
                                gift_value = self.gifts[gift_id]["pc"] / 100
                                logger.info(f"[Lv{level}] {nickname} 赠送了价值 {gift_value * int(gift_count)}¥ 的 {gift_name}*{int(gift_count)}")
                        except KeyError as e:
                            logger.error(f"礼物id:{e}不存在")
                        except Exception as e:
                            logger.error(e)
                            logger.info(f"收到礼物消息:{msg}")
                    else:
                        logger.debug(f"收到消息:{msg}")
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
    async def format_chatmsg_dict(cls, msg: str) -> dict:
        try:
            chatmsg_dict = dict(
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
            return chatmsg_dict
        except:  # noqa
            logger.error(f"奇怪的msg:{msg}")
            return {}
