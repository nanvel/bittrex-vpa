import aiohttp_jinja2
import sqlalchemy as sa

from vpa.db.trades import TradesTable


async def market_handler(request):
    market = request.match_info.get('market')

    lines = []
    points = []

    async with request.app['pg'].acquire() as conn:
        async for row in conn.execute(
                TradesTable.select().where(
                    sa.and_(
                        TradesTable.c.order_type == 'BUY',
                        TradesTable.c.market == market
                    )
                ).order_by(TradesTable.c.timestamp).limit(200)):
            points.append({'x': row.timestamp.isoformat(), 'y': row.quantity})

    lines.append({'label': 'Buy', 'data': points, 'borderColor': '#e6194b'})

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
