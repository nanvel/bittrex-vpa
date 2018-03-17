from functools import partial

import dateutil.parser
from aiopg.sa import create_engine

from vpa import settings
from vpa.bittrex import BittrexAPI
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


async def main(market):
    db_engine = await create_engine(
        dsn='dbname={db} user={user} password={password} host={host}'.format(
            db=settings.PG_DB,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            host=settings.PG_HOST
        )
    )

    api = BittrexAPI()

    try:
        await api.socket([market], partial(on_trades, db_engine=db_engine))
    finally:
        db_engine.close()
        await db_engine.wait_closed()
