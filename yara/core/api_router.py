import typing as tp

from fastapi import APIRouter, Depends, Request, Response  # noqa: F401


async def get_root_app(request: Request) -> tp.Any:
    return request.app.extra["yara_root_app"]


class YaraApiRouter(APIRouter):
    ...
