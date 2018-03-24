import datetime
import json

import aiohttp_jinja2
import dateutil.parser
import sqlalchemy as sa

from vpa.db.minutes import MinutesTable
from vpa.utils import COLORS


def parse_period(query):
    start = query.get('start', '')
    stop = query.get('stop', '')
    period = query.get('period', '')

    if period:
        period = datetime.timedelta(hours=int(period))
    else:
        period = datetime.timedelta(hours=2)

    if start:
        start = dateutil.parser.parse(start)
    else:
        start = datetime.datetime.utcnow() - period

    if stop:
        stop = dateutil.parser.parse(stop)
    else:
        stop = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    return start, stop


async def minutes_handler(request):
    market = request.match_info.get('market')
    start, stop = parse_period(query=request.rel_url.query)

    vsell = []
    vbuy = []
    rsell = []
    rbuy = []

    async with request.app['pg'].acquire() as conn:
        async for row in conn.execute(
                MinutesTable.select().where(
                    sa.and_(
                        MinutesTable.c.market == market,
                        MinutesTable.c.timestamp >= start,
                        MinutesTable.c.timestamp < stop
                    )
                ).order_by(MinutesTable.c.timestamp)):
            x = row.timestamp.isoformat()
            vsell.append({'x': x, 'y': -row.vsell})
            vbuy.append({'x': x, 'y': row.vbuy})
            rsell.append({'x': x, 'y': row.ratesell})
            rbuy.append({'x': x, 'y': row.ratebuy})

    datasets = [{
        'label': 'Sell volume',
        'borderColor': COLORS[0],
        'backgroundColor': 'rgba(200, 200, 200, 0.5)',
        'fill': True,
        'data': vsell,
        'yAxisID': 'y-axis-2',
    }, {
        'label': 'Buy volume',
        'borderColor': COLORS[1],
        'backgroundColor': 'rgba(200, 200, 200, 0.5)',
        'fill': True,
        'data': vbuy,
        'yAxisID': 'y-axis-2',
    }, {
        'label': 'Sell rate',
        'borderColor': COLORS[2],
        'backgroundColor': COLORS[2],
        'fill': False,
        'data': rsell,
        'yAxisID': 'y-axis-1'
    }, {
        'label': 'Buy rate',
        'borderColor': COLORS[3],
        'backgroundColor': COLORS[3],
        'fill': False,
        'data': rbuy,
        'yAxisID': 'y-axis-1'
    }]

    return aiohttp_jinja2.render_template(
        'minutes.j2',
        request,
        {'datasets': json.dumps(datasets)}
    )
