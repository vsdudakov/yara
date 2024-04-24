import logging
import socket
from typing import Any

import secure
from fastapi.security.utils import get_authorization_scheme_param
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware  # noqa: F401
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware  # noqa: F401
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware  # noqa: F401

logger = logging.getLogger(__name__)


class HostIPPlugin(plugins.Plugin):
    key = "host-ip"

    async def process_request(self, _: Request | HTTPConnection) -> Any | None:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)


class RefererPlugin(plugins.Plugin):
    key = "referer"


class AuthorizationPlugin(plugins.Plugin):
    key = "authorization"


class TokenPlugin(plugins.Plugin):
    key = "token"

    async def process_request(self, request: Request | HTTPConnection) -> Any | None:
        authorization = request.headers.get("authorization")
        _, token = get_authorization_scheme_param(authorization)
        return token if token else None


class SecureBaseMiddleware(BaseHTTPMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = None
        if scope["type"] in ("http",):
            request = Request(scope, receive, send)

        try:
            await super().__call__(scope, receive, send)
        except RuntimeError as e:
            if not request or not await request.is_disconnected():
                raise e
            return

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raise NotImplementedError()


class SecureMiddleware(SecureBaseMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        secure_headers: secure.Secure = secure.Secure(),
    ):
        super().__init__(app)
        self.secure_headers = secure_headers

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        self.secure_headers.framework.fastapi(response)
        return response


class SecureExtendedMiddleware(SecureBaseMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        header: str,
        value: str,
        policies: list[str] | dict[str, str],
        sep: str = "; ",
    ) -> None:
        super().__init__(app)
        self.header = header
        self.value = value
        self.policies = policies
        self.sep = sep

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if any(val in self.value for val in self.policies):
            response.headers[self.header] = self.value
        else:
            options = [(pol + self.sep) for pol in self.policies]
            raise SyntaxError(f"{self.header} has {len(self.policies)} options: {options}")
        return response
