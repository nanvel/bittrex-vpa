import asyncio
import hashlib
import hmac
import json
import time
from urllib.parse import urljoin, urlencode

import aiohttp
import async_timeout
import cfscrape


class BittrexError(Exception):

    def __init__(self, message):
        self.message = message


class BittrexAPI:
    """
    https://github.com/ericsomdahl/python-bittrex/blob/master/bittrex/bittrex.py
    https://bittrex.com/home/api
    """

    API_URL = 'https://bittrex.com/api/'
    MIN_TRADE_SIZE_BTC = 0.0005
    SOCKET_URL_ALT = 'https://socket-stage.bittrex.com/signalr'
    SOCKET_URL = 'https://socket.bittrex.com/signalr/'
    SOCKET_HUB = 'corehub'

    def __init__(self, api_key=None, api_secret=None, call_rate=1):
        self.api_key = api_key or ''
        self.api_secret = api_secret or ''
        self.call_interval = 1. / call_rate
        self.timeout = 20
        self._last_call = time.time() - self.call_interval

    async def socket(self, tickers, on_trades):
        """
        Uses signalr protocol: https://github.com/TargetProcess/signalr-client-py
        https://github.com/slazarov/python-bittrex-websocket/blob/master/bittrex_websocket/websocket_client.py
        """
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
                for n, ticker in enumerate(tickers, start=1):
                    message = {
                        'H': self.SOCKET_HUB,
                        'M': 'SubscribeToExchangeDeltas',
                        'A': [ticker],
                        'I': n
                    }
                    await ws.send_str(json.dumps(message))
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if 'M' in data:
                            for block in data['M']:
                                if block['M'] == 'updateExchangeState':
                                    for change in block['A']:
                                        fills = change['Fills']
                                        if fills:
                                            await on_trades(market=change['MarketName'], trades=fills)

    async def query(self, path, options=None, authenticate=False, priority=False, version='v1.1'):
        options = options or {}

        if path.startswith('/'):
            path = path[1:]
        url = urljoin(self.API_URL + version + '/', path)

        if authenticate:
            nonce = str(int(time.time() * 1000))
            url = "{url}?apikey={api_key}&nonce={nonce}".format(
                url=url, api_key=self.api_key, nonce=nonce
            )
            if options:
                url += '&' + urlencode(options)
        elif options:
            url += '?' + urlencode(options)

        signature = hmac.new(
            key=self.api_secret.encode(),
            msg=url.encode(),
            digestmod=hashlib.sha512
        ).hexdigest()

        if not priority:
            to_wait = time.time() - self._last_call + self.call_interval
            if to_wait > 0:
                await asyncio.sleep(to_wait)

        try:
            async with aiohttp.ClientSession(headers={'apisign': signature}) as session:
                with async_timeout.timeout(self.timeout):
                    async with session.get(url) as response:
                        j = await response.json()
                        if not j['success']:
                            raise BittrexError(
                                message="Bittrex API error - {}".format(
                                    j.get('message', "Unknown error.")
                                )
                            )
                        return j['result']
        finally:
            self._last_call = time.time()

    def get_markets(self):
        return self.query(path='/public/getmarkets')

    def get_currencies(self):
        return self.query(path='/public/getcurrencies')

    def get_ticker(self, market):
        return self.query(path='/public/getticker', options={'market': market})

    def get_tickers(self, market, interval):
        """ intervals: oneMin, fiveMin, hour, day  """
        return self.query(
            path='/pub/market/GetTicks',
            options={'marketName': market, 'tickInterval': interval},
            version='v2.0'
        )

    def get_market_summaries(self):
        return self.query(path='/public/getmarketsummaries')

    def get_market_summary(self, market):
        return self.query(path='/public/getmarketsummary', options={'market': market})

    def get_order_book(self, market, order_type='both'):
        """
        :param order_type: 'buy', 'sell', 'both'
        """
        return self.query(
            path='/public/getorderbook',
            options={'market': market, 'type': order_type}
        )

    def get_market_history(self, market):
        return self.query(path='/public/getmarkethistory', options={'market': market})

    def buy_limit(self, market, quantity, rate):
        return self.query(
            path='/market/buylimit',
            options={'market': market, 'quantity': quantity, 'rate': rate},
            authenticate=True,
            priority=True
        )

    def sell_limit(self, market, quantity, rate):
        return self.query(
            path='/market/selllimit',
            options={'market': market, 'quantity': quantity, 'rate': rate},
            authenticate=True,
            priority=True
        )

    def cancel_trade(self, order_id):
        return self.query(
            path='/market/cancel',
            options={'uuid': order_id},
            authenticate=True
        )

    def get_open_orders(self, market=None):
        return self.query(
            path='/market/getopenorders',
            options={'market': market} if market else None,
            authenticate=True
        )

    def get_balances(self):
        return self.query(
            path='/account/getbalances',
            authenticate=True
        )

    def get_balance(self, currency):
        return self.query(
            path='/account/getbalance',
            options={'currency': currency},
            authenticate=True
        )

    def get_deposit_address(self, currency):
        return self.query(
            path='/account/getdepositaddress',
            options={'currency': currency},
            authenticate=True
        )

    def withdraw(self, currency, quantity, address):
        return self.query(
            path='/account/getorderhistory',
            options={'currency': currency, 'quantity': quantity, 'address': address},
            authenticate=True
        )

    def get_order_history(self, market=None):
        return self.query(
            path='/account/getorderhistory',
            options={'market': market} if market else None,
            authenticate=True
        )

    def get_order(self, order_id):
        return self.query(
            path='/account/getorder',
            options={'uuid': order_id},
            authenticate=True
        )

    def get_withdrawal_history(self, currency=None):
        return self.query(
            path='/account/getwithdrawalhistory',
            options={'currency': currency} if currency else None,
            authenticate=True
        )

    def get_deposit_history(self, currency=None):
        return self.query(
            path='/account/getdeposithistory',
            options={'currency': currency} if currency else None,
            authenticate=True
        )
