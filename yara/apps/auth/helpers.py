import datetime
import logging
import secrets
import typing as tp
from uuid import UUID

import jwt
from passlib.context import CryptContext

from yara.adapters.orm.adapter import ORMAdapter, where_clause
from yara.apps.auth.models import User
from yara.core.api_router import Depends, HTTPException, Request, WebSocket, get_root_app, status
from yara.settings import YaraSettings

logger = logging.getLogger(__name__)


def generate_random_string(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def encode_jwt_token(
    payload: dict[str, tp.Any],
    expired_at: int,
    secret_key: str,
    algorithm: str = "HS256",
) -> str:
    now = datetime.datetime.now(tz=datetime.UTC)
    expire = now + datetime.timedelta(seconds=expired_at)
    payload.update({"exp": expire})
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_jwt_token(
    token: str,
    secret_key: str,
) -> dict[str, str] | None:
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
        logger.exception("Invalid jwt token")
        return None


def validate_password(
    hashed_password: str,
    password: str,
    crypt_context_scheme: str = "bcrypt",
) -> bool:
    return CryptContext(schemes=crypt_context_scheme, deprecated="auto").verify(password, hashed_password)


def hash_password(
    password: str,
    crypt_context_scheme: str = "bcrypt",
) -> str:
    return CryptContext(schemes=crypt_context_scheme, deprecated="auto").hash(password)


def _get_authenticated_user_id(
    settings: YaraSettings,
    token: str | None,
) -> UUID:
    try:
        if not token:
            raise ValueError("Invalid Token")
        secret_key = settings.YARA_AUTH_SECRET_KEY
        payload = decode_jwt_token(token, secret_key)
        if not payload:
            raise ValueError("Invalid Token")
        return UUID(payload["id"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token") from None


async def get_authenticated_user_id(
    request: Request,
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    settings: YaraSettings = root_app.settings
    access_token = request.cookies.get("AccessToken")
    return _get_authenticated_user_id(settings, access_token)


async def get_authenticated_superuser_id(
    authenticated_user_id: UUID = Depends(get_authenticated_user_id),
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    orm_adapter: ORMAdapter[User] = root_app.get_adapter(ORMAdapter)
    if not await orm_adapter.exists(User, where_clause(id=str(authenticated_user_id), is_superuser=True)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Superuser Not Found")
    return authenticated_user_id


async def get_authenticated_group_id(
    authenticated_user_id: UUID = Depends(get_authenticated_user_id),
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    orm_adapter: ORMAdapter[User] = root_app.get_adapter(ORMAdapter)
    user = await orm_adapter.read(User, where_clause(id=str(authenticated_user_id)))
    if not user or not user.group_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Group Not Found")
    return user.group_id


async def get_ws_authenticated_user_id(
    websocket: WebSocket,
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    settings: YaraSettings = root_app.settings
    access_token = websocket.cookies.get("AccessToken")
    return _get_authenticated_user_id(settings, access_token)


async def get_authenticated_user_id_from_refresh(
    request: Request,
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    settings: YaraSettings = root_app.settings
    refresh_token = request.cookies.get("RefreshToken")
    return _get_authenticated_user_id(settings, refresh_token)
