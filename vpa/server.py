from aiohttp import web

from vpa import settings
from vpa.db import pg_init, pg_close
from vpa.handlers.analysis import analysis_handler
from vpa.handlers.bubbles import bubbles_handler
from vpa.handlers.export import export_handler
from vpa.handlers.index import index_handler
from vpa.handlers.market import market_handler
from vpa.handlers.minutes import minutes_handler
from vpa.utils import jinja_setup


def main():
    app = web.Application()
    app.on_startup.append(jinja_setup)
    app.on_startup.append(pg_init)
    app.on_cleanup.append(pg_close)

    app.router.add_get('/', index_handler)
    app.router.add_get('/markets/{market:\w{2,5}-\w{2,5}}', market_handler)
    app.router.add_get('/markets/{market:\w{2,5}-\w{2,5}}/analysis', analysis_handler)
    app.router.add_get('/markets/{market:\w{2,5}-\w{2,5}}/bubbles', bubbles_handler)
    app.router.add_get('/markets/{market:\w{2,5}-\w{2,5}}/minutes', minutes_handler)
    app.router.add_get('/markets/{market:\w{2,5}-\w{2,5}}/export', export_handler)

    if settings.ENV == 'development':
        app.router.add_static('/logs', settings.LOGS_DIR)

    web.run_app(app, port=int(settings.SERVER_PORT))
