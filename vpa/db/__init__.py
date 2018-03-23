from aiopg.sa import create_engine

from vpa import settings

from .base import metadata
from .minutes import MinutesTable
from .trades import TradesTable


async def pg_init(app):
    app['pg'] = await create_engine(
        dsn='dbname={db} user={user} password={password} host={host}'.format(
            db=settings.PG_DB,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            host=settings.PG_HOST
        )
    )


async def pg_close(app):
    app['pg'].close()
    await app['pg'].wait_closed()
