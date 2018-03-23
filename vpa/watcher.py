import asyncio
import datetime
from collections import defaultdict
from functools import partial

import dateutil.parser
import sqlalchemy as sa
from aiopg.sa import create_engine

from vpa import settings
from vpa.bittrex import BittrexTradesSocket
from vpa.db.minutes import MinutesTable
from vpa.db.trades import TradesTable


async def on_trades(market, trades, db_engine):
    async with db_engine.acquire() as conn:
        for trade in trades:
            await conn.execute(TradesTable.insert().values(
                market=market,
                order_type=trade['OrderType'],
                rate=trade['Rate'],
                quantity=trade['Quantity'],
                timestamp=dateutil.parser.parse(trade['TimeStamp'])
            )
        )


async def minutes_dump(db_engine):
    """
    Count last 2 minutes, update db.
    """
    while True:
        await asyncio.sleep(10)
        current_markets = defaultdict(lambda: {
            'vsell': 0,
            'vbuy': 0,
            'nsell': 0,
            'nbuy': 0,
            'ratesell': None,
            'ratebuy': None
        })
        previous_markets = defaultdict(lambda: {
            'vsell': 0,
            'vbuy': 0,
            'nsell': 0,
            'nbuy': 0,
            'ratesell': None,
            'ratebuy': None
        })
        async with db_engine.acquire() as conn:
            current_minute = datetime.datetime.utcnow().replace(second=0, microsecond=0)
            previous_minute = current_minute - datetime.timedelta(minutes=1)
            next_minute = current_minute + datetime.timedelta(minutes=1)
            async for row in conn.execute(
                    TradesTable.select().where(
                        sa.and_(
                            TradesTable.c.timestamp >= current_minute,
                            TradesTable.c.timestamp < next_minute
                        )
                    ).order_by(sa.asc(TradesTable.c.timestamp))):
                current_market = current_markets[row.market]
                if row.order_type == 'BUY':
                    current_market['vbuy'] += row.quantity
                    current_market['nbuy'] += 1
                    current_market['ratebuy'] = row.rate
                elif row.order_type == 'SELL':
                    current_market['vsell'] += row.quantity
                    current_market['nsell'] += 1
                    current_market['ratesell'] = row.rate
            async for row in conn.execute(
                    TradesTable.select().where(
                        sa.and_(
                            TradesTable.c.timestamp >= previous_minute,
                            TradesTable.c.timestamp < current_minute
                        )
                    ).order_by(sa.asc(TradesTable.c.timestamp))):
                previous_market = previous_markets[row.market]
                if row.order_type == 'BUY':
                    previous_market['vbuy'] += row.quantity
                    previous_market['nbuy'] += 1
                    previous_market['ratebuy'] = row.rate
                elif row.order_type == 'SELL':
                    previous_market['vsell'] += row.quantity
                    previous_market['nsell'] += 1
                    previous_market['ratesell'] = row.rate

            if not current_markets and not previous_markets:
                continue

            existing = []
            async for row in conn.execute(
                    MinutesTable.select().where(
                        sa.and_(
                            TradesTable.c.timestamp >= previous_minute,
                            TradesTable.c.timestamp < next_minute
                        )
                    )):
                existing.append((row.market, row.timestamp))

            for markets, timestamp in ((current_markets, current_minute), (previous_markets, previous_minute)):
                for market, minute in markets.items():
                    if (market, timestamp) in existing:
                        await conn.execute(MinutesTable.update().values(
                            vsell=minute['vsell'],
                            vbuy=minute['vbuy'],
                            nsell=minute['nsell'],
                            nbuy=minute['nbuy'],
                            ratesell=minute['ratesell'],
                            ratebuy=minute['ratebuy']
                        ).where(
                            sa.and_(
                                MinutesTable.c.market == market,
                                MinutesTable.c.timestamp == timestamp
                            )
                        ))
                    else:
                        await conn.execute(MinutesTable.insert().values(
                            market=market,
                            timestamp=timestamp,
                            vsell=minute['vsell'],
                            vbuy=minute['vbuy'],
                            nsell=minute['nsell'],
                            nbuy=minute['nbuy'],
                            ratesell=minute['ratesell'],
                            ratebuy=minute['ratebuy']
                        ))


async def main(markets):
    db_engine = await create_engine(
        dsn='dbname={db} user={user} password={password} host={host}'.format(
            db=settings.PG_DB,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            host=settings.PG_HOST
        )
    )

    trades_socket = BittrexTradesSocket(
        tickers=markets,
        on_trades=partial(on_trades, db_engine=db_engine)
    )

    minutes_task = asyncio.ensure_future(minutes_dump(db_engine=db_engine))

    try:
        await trades_socket.run()
    finally:
        minutes_task.cancel()
        db_engine.close()
        await db_engine.wait_closed()
