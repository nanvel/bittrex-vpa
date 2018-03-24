import sqlalchemy as sa
from aiohttp import web

from vpa.db.trades import TradesTable

from .minutes import parse_period


async def export_handler(request):
    market = request.match_info.get('market')
    start, stop = parse_period(query=request.rel_url.query)

    trades = []
    async with request.app['pg'].acquire() as conn:
        async for row in conn.execute(
                TradesTable.select().where(
                    sa.and_(
                        TradesTable.c.market == market,
                        TradesTable.c.timestamp >= start,
                        TradesTable.c.timestamp < stop
                    )
                ).order_by(TradesTable.c.timestamp)):
            trades.append({
                'order_type': row.order_type,
                'rate': row.rate,
                'quantity': row.quantity,
                'timestamp': row.timestamp.isoformat()
            })

    return web.json_response({
        'trades': trades,
        'market': market,
        'start': start.isoformat(),
        'stop': stop.isoformat()
    })
