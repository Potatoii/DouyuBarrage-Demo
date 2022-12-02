import datetime

from commons.log_utils import logger


async def console_log(barrage_dict: dict):
    if barrage_dict.get("bnn"):
        logger.info(
            f"[Lv{barrage_dict.get('level')}]【{barrage_dict.get('bnn')}】{barrage_dict.get('nickname')}:{barrage_dict.get('content')}")
    else:
        logger.info(f"[Lv{barrage_dict.get('level')}]{barrage_dict.get('nickname')}:{barrage_dict.get('content')}")


async def check_superchat(barrage_dict: dict):
    content = barrage_dict.get("content")
    if content.startswith("【") and content.endswith("】"):
        msg = f"{datetime.datetime.now():%y-%m-%d %H:%M:%S}|{barrage_dict.get('nickname')}标记:{content}"
        logger.info(msg)
