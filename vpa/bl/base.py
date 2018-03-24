from vpa.db.trades import TradeMapper


class Trades:

    STORAGE_LIMIT = 2000

    def __init__(self):
        self._trades = []

    def add_trade(self, timestamp, order_type, quantity, rate):
        self._trades.append({
            't': timestamp,
            'ot': order_type,
            'q': quantity,
            'r': rate
        })
        if len(self._trades) > self.STORAGE_LIMIT:
            self._trades = self._trades[round(self.STORAGE_LIMIT / 20):]

    def get(self, start, stop):
        sells = []
        buys = []
        for t in self._trades:
            if stop > t['t'] >= start:
                if t['ot'] == TradeMapper.ORDER_TYPE_BUY:
                    buys.append(t)
                elif t['ot'] == TradeMapper.ORDER_TYPE_SELL:
                    sells.append(t)
        buys = list(sorted(buys, key=lambda i: i['t']))
        sells = list(sorted(sells, key=lambda i: i['t']))
        return {
            'buys': buys,
            'sells': sells
        }

    def get_stats(self, start, stop):
        trades = self.get(start=start, stop=stop)
        sells = trades['sells']
        buys = trades['buys']
        return {
            'nsell': len(sells),
            'nbuy': len(buys),
            'vsell': sum([i['q'] for i in sells]),
            'vbuy': sum([i['q'] for i in buys]),
            'osell': sells[0]['r'],
            'csell': sells[-1]['r'],
            'obuy': buys[0]['r'],
            'cbuy': buys[-1]['r']
        }


class Decision:

    def __init__(self, timestamp, rate):
        self.timestamp = timestamp
        self.rate = rate
        self.do = None
        self.indicators = {}

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'rate': self.rate,
            'do': self.do,
            'indicators': self.indicators
        }


class StrategyRegistry:

    _strategies = {}

    @classmethod
    def register(cls, item):
        if item.NAME:
            cls._strategies[item.NAME] = item

    @classmethod
    def list(cls):
        return cls._strategies.keys()

    @classmethod
    def get(cls, name):
        return cls._strategies.get(name)


class StrategyMeta(type):

    NAME = None

    def __init__(cls, name, bases, attrs):
        super(StrategyMeta, cls).__init__(name, bases, attrs)
        StrategyRegistry.register(item=cls)


class BaseStrategy(metaclass=StrategyMeta):

    def __init__(self):
        self._trades = Trades()

    def get_trades(self):
        return self._trades

    def set_trades(self, trades):
        self._trades = trades

    def decide(self, decision):
        return decision

    def add_trade(self, timestamp, order_type, quantity, rate):
        self._trades.add_trade(
            timestamp=timestamp,
            order_type=order_type,
            quantity=quantity,
            rate=rate
        )
        return self.decide(Decision(timestamp=timestamp, rate=rate))
