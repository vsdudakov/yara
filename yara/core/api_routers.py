import typing as tp
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, WebSocket, status  # noqa: F401

from yara.core.helpers import decode_jwt_token
from yara.settings import YaraSettings


async def get_root_app(request: Request) -> tp.Any:
    return request.app.extra["yara_root_app"]


def get_service(service_cls: type[tp.Any], **kwargs: tp.Any) -> tp.Any:
    async def service(root_app: tp.Any = Depends(get_root_app)) -> tp.Any:
        return service_cls(root_app, **kwargs)

    return service


class YaraApiRouter(APIRouter):
    ...


def _get_authenticated_user_id(
    settings: YaraSettings,
    token: str | None,
) -> uuid.UUID:
    try:
        if not token:
            raise ValueError("Invalid Token")
        secret_key = settings.YARA_AUTH_SECRET_KEY
        payload = decode_jwt_token(token, secret_key)
        if not payload:
            raise ValueError("Invalid Token")
        return uuid.UUID(payload["id"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token") from None


async def get_authenticated_user_id(
    request: Request,
    root_app: tp.Any = Depends(get_root_app),
) -> uuid.UUID:
    settings: YaraSettings = root_app.settings
    access_token = request.cookies.get("AccessToken")
    return _get_authenticated_user_id(settings, access_token)


async def get_ws_authenticated_user_id(
    websocket: WebSocket,
    root_app: tp.Any = Depends(get_root_app),
) -> uuid.UUID:
    settings: YaraSettings = root_app.settings
    access_token = websocket.cookies.get("AccessToken")
    return _get_authenticated_user_id(settings, access_token)


async def get_authenticated_user_id_from_refresh(
    request: Request,
    root_app: tp.Any = Depends(get_root_app),
) -> uuid.UUID:
    settings: YaraSettings = root_app.settings
    refresh_token = request.cookies.get("RefreshToken")
    return _get_authenticated_user_id(settings, refresh_token)
