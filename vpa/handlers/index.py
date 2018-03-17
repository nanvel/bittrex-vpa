import aiohttp_jinja2


async def index_handler(request):
    return aiohttp_jinja2.render_template(
        'index.j2',
        request,
        {}
    )
