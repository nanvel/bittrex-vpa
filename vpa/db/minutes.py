import sqlalchemy as sa
from sqlalchemy.orm import mapper

from .base import metadata


MinutesTable = sa.Table(
    'minutes',
    metadata,
    sa.Column('market', sa.String(10), primary_key=True),
    sa.Column('timestamp', sa.DateTime(), primary_key=True),
    sa.Column('vsell', sa.Float()),
    sa.Column('vbuy', sa.Float()),
    sa.Column('nsell', sa.Integer()),
    sa.Column('nbuy', sa.Integer()),
    sa.Column('ratesell', sa.Float(), nullable=True),  # last sell/buy rates
    sa.Column('ratebuy', sa.Float(), nullable=True)
)


class MinuteMapper:
    def __init__(self, market, timestamp, vsell, vbuy, ratesell, ratebuy):
        self.market = market
        self.timestamp = timestamp
        self.vsell = vsell
        self.vbuy = vbuy
        self.ratesell = ratesell
        self.ratebuy = ratebuy


mapper(MinuteMapper, MinutesTable)
