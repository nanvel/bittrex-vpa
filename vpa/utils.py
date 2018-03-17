import os.path

import aiohttp_jinja2
import jinja2


PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def rel(*path):
    return os.path.join(PROJECT_ROOT, *path)


async def jinja_setup(app):
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(rel('vpa/templates'))
    )
