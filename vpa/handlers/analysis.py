import datetime

import sqlalchemy as sa
import aiohttp_jinja2
from sqlalchemy.sql import func

from vpa.db.trades import TradesTable


async def vpa(conn, market, period, order_type):
    last_trade = await (
        await conn.execute(
            TradesTable.select().where(
                sa.and_(
                    TradesTable.c.market == market,
                    TradesTable.c.order_type == order_type
                )
            ).order_by(
                sa.desc(TradesTable.c.timestamp)
            )
        )
    ).first()

    from_rate = last_trade.rate * 0.95
    to_rate = last_trade.rate * 1.05

    result = {}
    previous_level = 0
    for i in range(10):
        level = from_rate + (to_rate - from_rate) / 10 * i

        result[level] = await conn.scalar(
            sa.select([func.sum(TradesTable.c.quantity)]).where(
                sa.and_(
                    TradesTable.c.market == market,
                    TradesTable.c.timestamp >= (
                            datetime.datetime.utcnow() - datetime.timedelta(hours=period)
                    ),
                    TradesTable.c.rate > previous_level,
                    TradesTable.c.rate <= level,
                    TradesTable.c.order_type == order_type
                )
            )
        )
        previous_level = level

    result[previous_level] = await conn.scalar(
        sa.select([func.sum(TradesTable.c.quantity)]).where(
            sa.and_(
                TradesTable.c.market == market,
                TradesTable.c.timestamp >= (
                        datetime.datetime.utcnow() - datetime.timedelta(hours=period)
                ),
                TradesTable.c.rate > previous_level,
                TradesTable.c.order_type == order_type
            )
        )
    )

    return result


async def analysis_handler(request):
    market = request.match_info.get('market')
    period_hrs = int(request.rel_url.query.get('period', 1))  # hrs

    async with request.app['pg'].acquire() as conn:
        buy_result = await vpa(conn=conn, market=market, period=period_hrs, order_type='BUY')
        sell_result = await vpa(conn=conn, market=market, period=period_hrs, order_type='SELL')

    points = []
    for price, volume in buy_result.items():
        points.append({'x': price, 'y': volume or 0, 'c': 'rgba(255, 99, 132, 0.2)'})

    for price, volume in sell_result.items():
        points.append({'x': price, 'y': volume or 0, 'c': 'rgba(75, 192, 192, 0.2)'})

    points = sorted(points, key=lambda i: i['x'])

    values = '[' + ', '.join([str(p['y']) for p in points]) + ']'
    labels = '[' + ', '.join([str(p['x']) for p in points]) + ']'
    colors = '[' + ', '.join(['"' + p['c'] + '"' for p in points]) + ']'

    data = """{{
    "labels": {labels},
    "datasets": [
        {{
            "label": "VPA",
            "data": {values},
            "backgroundColor": {colors}
        }}
    ]
}}""".format(labels=labels, values=values, colors=colors)

    return aiohttp_jinja2.render_template(
        'analysis.j2',
        request,
        {'data': data}
    )
