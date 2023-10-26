import asyncio
import json

import httpx

import settings
from commons.log_utils import logger


class Gift:
    def __init__(self):
        self.backpack_gifts_url = "https://webconf.douyucdn.cn/resource/common/prop_gift_list/prop_gift_config.json"
        self.rmb_gifts_url = f"https://gift.douyucdn.cn/api/gift/v2/web/list?rid={settings.ROOM_ID}"
        self.backpack_gifts = {}
        self.rmb_gifts = {}
        self.gifts = {}

    async def get_backpack_gifts(self):
        """
        获取背包礼物列表
        """
        async with httpx.AsyncClient() as request:
            response = await request.get(self.backpack_gifts_url)
            if response.status_code == 200:
                response_json = json.loads(
                    response.text.replace("DYConfigCallback(", "").replace(");", "")
                )
                self.backpack_gifts = response_json["data"]
            else:
                logger.error("获取背包礼物列表失败")

    async def get_rmb_gifts(self):
        """
        获取鱼翅礼物列表
        """
        async with httpx.AsyncClient() as request:
            response = await request.get(self.rmb_gifts_url)
            if response.status_code == 200:
                response_json = response.json()
                for response_gift in response_json["data"]["giftList"]:
                    if response_gift["priceInfo"]["priceType"] == "YUCHI":
                        self.rmb_gifts[str(response_gift["id"])] = {
                            "name": response_gift["name"],
                            "pc": response_gift["priceInfo"]["price"]
                        }
                    else:
                        self.rmb_gifts[str(response_gift["id"])] = {
                            "name": response_gift["name"],
                            "pc": response_gift["priceInfo"]["price"] / 100
                        }
            else:
                logger.error("获取RMB礼物列表失败")

    async def init_gifts(self):
        functions = [self.get_backpack_gifts(), self.get_rmb_gifts()]
        await asyncio.gather(*functions)
        self.gifts = {**self.backpack_gifts, **self.rmb_gifts}


if __name__ == "__main__":
    g = Gift()
    asyncio.run(g.init_gifts())
    print(g.gifts)
