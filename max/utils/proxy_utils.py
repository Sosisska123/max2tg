import logging

import websockets

logger = logging.getLogger(__name__)

PROXIES = [
    "http://94.232.11.178:3128",
    "http://195.133.14.14:8080",
    "http://91.188.244.133:8080",
]


async def check_proxy():
    for proxy in PROXIES:
        try:
            async with websockets.connect(
                "wss://ifconfig.me",
                proxy=proxy,
                timeout=8,
            ) as ws:
                await ws.send("")
                ip = await ws.recv()
                logger.info("Рабочий прокси: %s -> IP: %s", proxy, ip)
                return proxy
        except Exception as e:
            logger.error("× %s — не работает (%s)", proxy, e)
    raise Exception("Все прокси мертвы :(")


async def try_get_working_proxy():
    return await check_proxy()
