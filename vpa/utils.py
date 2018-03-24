import os.path

import aiohttp_jinja2
import jinja2


PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

COLORS = (
    '#e6194b',
    '#3cb44b',
    '#ffe119',
    '#0082c8',
    '#f58231',
    '#911eb4',
    '#46f0f0',
    '#f032e6',
    '#d2f53c',
    '#fabebe',
    '#008080',
    '#e6beff',
    '#aa6e28',
    '#fffac8',
    '#800000',
    '#aaffc3',
    '#808000',
    '#ffd8b1',
    '#000080'
)


def rel(*path):
    return os.path.join(PROJECT_ROOT, *path)


async def jinja_setup(app):
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(rel('vpa/templates'))
    )
