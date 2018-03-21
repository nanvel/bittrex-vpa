import json

import aiohttp_jinja2
import sqlalchemy as sa

from vpa.db.trades import TradesTable


async def bubbles_handler(request):
    market = request.match_info.get('market')

    points_buy = []
    points_sell = []

    async with request.app['pg'].acquire() as conn:
        async for row in conn.execute(
                TradesTable.select().where(
                    TradesTable.c.market == market
                ).order_by(sa.desc(TradesTable.c.timestamp)).limit(400)):
            if row.order_type == 'BUY':
                points_buy.append({'x': row.timestamp.isoformat(), 'r': row.quantity * 5, 'y': row.rate})
            elif row.order_type == 'SELL':
                points_sell.append({'x': row.timestamp.isoformat(), 'r': row.quantity, 'y': row.rate})

    max_buy_volume = max([i['r'] for i in points_buy])
    for p in points_buy:
        p['r'] = p['r'] / max_buy_volume * 100

    max_sell_volume = max([i['r'] for i in points_sell])
    for p in points_sell:
        p['r'] = p['r'] / max_sell_volume * 100

    return aiohttp_jinja2.render_template(
        'bubbles.j2',
        request,
        {
            'data_buy': json.dumps(points_buy),
            'data_sell': json.dumps(points_sell)
        }
    )
