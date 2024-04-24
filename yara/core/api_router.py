import typing as tp

from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, status  # noqa: F401


async def get_root_app(request: Request) -> tp.Any:
    return request.app.extra["yara_root_app"]


def get_service(service_cls: type[tp.Any]) -> tp.Any:
    async def service(root_app: tp.Any = Depends(get_root_app)) -> tp.Any:
        return service_cls(root_app)

    return service


class YaraApiRouter(APIRouter):
    ...
