import asyncio

from sqlalchemy.engine import url
from sqlalchemy import util

from .engine import GinoEngine


async def create_engine(name_or_url, loop=None, engine_cls=None, **kwargs):
    if engine_cls is None:
        engine_cls = GinoEngine
    u = url.make_url(name_or_url)
    if loop is None:
        loop = asyncio.get_event_loop()
    if u.drivername in {'postgresql', 'postgres'}:
        u.drivername = 'postgresql+asyncpg'

    dialect_cls = u.get_dialect()

    pop_kwarg = kwargs.pop

    dialect_args = {}
    # consume dialect arguments from kwargs
    for k in util.get_cls_kwargs(dialect_cls).union(
            getattr(dialect_cls, 'init_kwargs', set())):
        if k in kwargs:
            dialect_args[k] = pop_kwarg(k)
    dialect = dialect_cls(**dialect_args)
    pool = await dialect.init_pool(u, loop)

    engine_args = dict(loop=loop)
    for k in util.get_cls_kwargs(engine_cls):
        if k in kwargs:
            engine_args[k] = pop_kwarg(k)

    # all kwargs should be consumed
    if kwargs:
        raise TypeError(
            "Invalid argument(s) %s sent to create_engine(), "
            "using configuration %s/%s.  Please check that the "
            "keyword arguments are appropriate for this combination "
            "of components." % (','.join("'%s'" % k for k in kwargs),
                                dialect_cls.__name__,
                                engine_cls.__name__))

    engine = engine_cls(dialect, pool, **engine_args)

    dialect_cls.engine_created(engine)

    return engine