import datetime
import logging
import secrets
import typing as tp
from importlib import import_module

import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


def import_obj(path: str) -> tp.Any | None:
    module, cls = path.rsplit(".", 1)
    try:
        command_module = import_module(module)
        return getattr(command_module, cls)
    except (ImportError, AttributeError) as e:
        logger.exception(e)
        return None


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
