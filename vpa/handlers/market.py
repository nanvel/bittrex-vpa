import aiohttp_jinja2
import sqlalchemy as sa

from vpa.db.trades import TradesTable


async def market_handler(request):
    market = request.match_info.get('market')

    lines = []
    points_buy = []
    points_sell = []

    async with request.app['pg'].acquire() as conn:
        async for row in conn.execute(
                TradesTable.select().where(
                    TradesTable.c.market == market
                ).order_by(sa.desc(TradesTable.c.timestamp)).limit(200)):
            if row.order_type == 'BUY':
                points_buy.append({'x': row.timestamp.isoformat(), 'y': row.quantity})
            elif row.order_type == 'SELL':
                points_sell.append({'x': row.timestamp.isoformat(), 'y': row.quantity})

    lines.append({'label': 'Buy', 'data': points_buy, 'borderColor': '#e6194b'})
    lines.append({'label': 'Sell', 'data': points_sell, 'borderColor': '#3cb44b'})

    datasets = '[' + ', '.join(
        ["{{label: '{label}', data: [{points}], borderColor: '{color}'}}".format(
            label=l['label'],
            points=', '.join([
                "{{x: '{date}', y: {value}}}".format(
                    date=p['x'],
                    value=p['y']
                ) for p in l['data']
            ]),
            color=l['borderColor']
        ) for l in lines]
    ) + ']'

    return aiohttp_jinja2.render_template(
        'market.j2',
        request,
        {'datasets': datasets}
    )
