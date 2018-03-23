import asyncio
import json
import logging
import time
from urllib.parse import urlencode

import aiohttp
import cfscrape


logger = logging.getLogger(__name__)


class BittrexTradesSocket:
    """
    https://github.com/ericsomdahl/python-bittrex/blob/master/bittrex/bittrex.py
    https://bittrex.com/home/api
    """
    SOCKET_URL = 'https://socket.bittrex.com/signalr/'
    SOCKET_HUB = 'corehub'
    RECONNECT_TIMEOUT = 300

    def __init__(self, tickers, on_trades):
        self.tickers = tickers
        self._ws = None
        self._last_message = None
        self.connected = False
        self.on_trades = on_trades
        self.listen_task = None
        self.connected = False

    async def run(self):
        self.listen_task = asyncio.ensure_future(self._listen())
        while True:
            await asyncio.sleep(round(self.RECONNECT_TIMEOUT / 10))
            if not self.connected:
                break
            if not self._ws:
                continue
            if self._last_message and time.time() - self._last_message > self.RECONNECT_TIMEOUT:
                await self._ws.close()
                self.listen_task.cancel()
                self._last_message = None
                self._ws = None
                self.listen_task = asyncio.ensure_future(self._listen())
                logger.warning("Socket was reconnected.")

    async def stop(self):
        self.connected = False
        self._last_message = None
        await self._ws.close()
        self.listen_task.cancel()
        self._ws = None

    async def _listen(self):
        """
        Uses signalr protocol: https://github.com/TargetProcess/signalr-client-py
        https://github.com/slazarov/python-bittrex-websocket/blob/master/bittrex_websocket/websocket_client.py
        """
        if self.connected:
            return
        conn_data = json.dumps([{'name': self.SOCKET_HUB}])
        url = self.SOCKET_URL + 'negotiate' + '?' + urlencode({
            'clientProtocol': '1.5',
            'connectionData': conn_data,
            '_': round(time.time() * 1000)
        })
        cookie_str, user_agent = cfscrape.get_cookie_string(url)
        async with aiohttp.ClientSession(headers={'User-Agent': user_agent, 'Cookie': cookie_str}) as session:
            async with session.get(url) as r:
                socket_conf = await r.json()

            socket_url = self.SOCKET_URL.replace('https', 'wss') + 'connect' + '?' + urlencode({
                'transport': 'webSockets',
                'clientProtocol': socket_conf['ProtocolVersion'],
                'connectionToken': socket_conf['ConnectionToken'],
                'connectionData': conn_data,
                'tid': 3
            })
            async with session.ws_connect(socket_url) as ws:
                self._ws = ws
                self.connected = True
                for n, ticker in enumerate(self.tickers, start=1):
                    message = {
                        'H': self.SOCKET_HUB,
                        'M': 'SubscribeToExchangeDeltas',
                        'A': [ticker],
                        'I': n
                    }
                    await ws.send_str(json.dumps(message))
                async for msg in ws:
                    self._last_message = time.time()
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if 'M' in data:
                            for block in data['M']:
                                if block['M'] == 'updateExchangeState':
                                    for change in block['A']:
                                        fills = change['Fills']
                                        if fills:
                                            await self.on_trades(market=change['MarketName'], trades=fills)
                    elif msg.tp == aiohttp.WSMsgType.closed:
                        break
                    elif msg.tp == aiohttp.WSMsgType.error:
                        break
            self._ws = None
            self.connected = False
