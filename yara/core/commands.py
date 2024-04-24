import asyncio
import typing as tp
from functools import wraps

from typer import Option, echo  # noqa: F401


def command(func: tp.Any) -> tp.Any:
    @wraps(func)
    def wrapper(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
        async def wrapped_func(*args: tp.Any, **kwargs: tp.Any) -> tp.Any:
            from yara.main import fastapi_app_lifespan, root_app

            async with fastapi_app_lifespan(root_app.get_asgi_app()):
                kwargs["root_app"] = root_app
                return await func(*args, **kwargs)

        return asyncio.run(wrapped_func(*args, **kwargs))

    return wrapper
