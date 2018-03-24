import sqlalchemy as sa
from sqlalchemy.orm import mapper

from .base import metadata


TradesTable = sa.Table(
    'trades',
    metadata,
    sa.Column('trade_id', sa.Integer, primary_key=True),  # autoincrement
    sa.Column('market', sa.String(10)),
    sa.Column('order_type', sa.String(4)),
    sa.Column('rate', sa.Float()),
    sa.Column('quantity', sa.Float()),
    sa.Column('timestamp', sa.DateTime()),
    sa.Index('idx_timestamp', 'timestamp', unique=False)
)


class TradeMapper:

    ORDER_TYPE_SELL = 'SELL'
    ORDER_TYPE_BUY = 'BUY'

    def __init__(self, trade_id, market, order_type, rate, quantity, timestamp):
        self.trade_id = trade_id
        self.market = market
        self.order_type = order_type
        self.rate = rate
        self.quantity = quantity
        self.timestamp = timestamp


mapper(TradeMapper, TradesTable)
