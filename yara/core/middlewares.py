from abc import abstractmethod

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class YaraMiddleware(BaseHTTPMiddleware):
    @abstractmethod
    async def process_request(self, request: Request) -> Request:
        """
        Process request before passing to the next middleware or endpoint.
        """
        ...

    @abstractmethod
    async def process_response(self, request: Request, response: Response) -> Response:
        """
        Process response before returning to the client.
        """
        ...

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request = await self.process_request(request)
        response = await call_next(request)
        return await self.process_response(request, response)
