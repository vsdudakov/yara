import datetime
import logging
import secrets
import typing as tp
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, WebSocket, status
from passlib.context import CryptContext

from yara.adapters.orm.adapter import ORMAdapter, where_clause
from yara.apps.auth.models import User
from yara.core.api_router import get_root_app

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


async def get_authenticated_user_id(
    authorization: str
    | None = Header(
        default=None,
        alias="Authorization",
        title="Access Token",
        example="Bearer <access_token>",
    ),
    access_token_cookie: str
    | None = Cookie(
        default=None,
        title="Access Token",
        example="<access_token>",
    ),
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    access_token = None
    if access_token_cookie:
        access_token = access_token_cookie
    elif authorization:
        access_token = authorization.replace("Bearer ", "")
    try:
        if not access_token:
            raise ValueError("Invalid Access Token")
        secret_key = root_app.settings.YARA_AUTH_SECRET_KEY
        payload = decode_jwt_token(access_token, secret_key)
        if not payload:
            raise ValueError("Invalid Access Token")
        return UUID(payload["id"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access Token") from None


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
    authorization: str
    | None = Header(
        default=None,
        alias="Authorization",
        title="Access Token",
        examples=["Bearer <access_token>"],
    ),
    access_token_cookie: str
    | None = Cookie(
        default=None,
        title="Access Token",
        examples=["<access_token>"],
    ),
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    try:
        return await get_authenticated_user_id(
            authorization=authorization,
            access_token_cookie=access_token_cookie,
            root_app=root_app,
        )
    except HTTPException as exc:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid Access Token")
        raise exc


async def get_authenticated_user_id_from_refresh(
    authorization: str
    | None = Header(
        default=None,
        alias="Authorization",
        title="Refresh Token",
        examples=["Bearer <refresh_token>"],
    ),
    refresh_token_cookie: str
    | None = Cookie(
        default=None,
        title="Refresh Token",
        examples=["<refresh_token>"],
    ),
    root_app: tp.Any = Depends(get_root_app),
) -> UUID:
    refresh_token = None
    if refresh_token_cookie:
        refresh_token = refresh_token_cookie
    elif authorization:
        refresh_token = authorization.replace("Bearer ", "")
    try:
        if not refresh_token:
            raise ValueError("Invalid Access Token")
        secret_key = root_app.settings.YARA_JWT_SECRET_KEY
        payload = decode_jwt_token(refresh_token, secret_key)
        if not payload:
            raise ValueError("Invalid Refresh Token")
        return UUID(payload["id"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh Token") from None
