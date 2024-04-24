from enum import StrEnum

from yara.adapters.oauth.backends.base import OAuth2Backend
from yara.adapters.oauth.backends.google import GoogleOAuth2Backend
from yara.core.adapters import YaraAdapter
from yara.main import YaraBaseRootApp


class OAuth2BackendEnum(StrEnum):
    GOOGLE = "google"


class OAuth2Adapter(YaraAdapter):
    root_app: YaraBaseRootApp

    async def up(self) -> None:
        pass

    async def healthcheck(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass

    def get_backend(self, backend: OAuth2BackendEnum) -> OAuth2Backend | None:
        match backend:
            case OAuth2BackendEnum.GOOGLE:
                return GoogleOAuth2Backend(self.root_app.settings)
            case _:
                return None

    async def get_authorization_url(
        self,
        backend_type: OAuth2BackendEnum,
        redirect_uri: str,
    ) -> str | None:
        backend = self.get_backend(backend_type)
        if backend is None:
            return None
        return await backend.get_authorization_url(redirect_uri)

    async def get_user_email_from_provider(
        self,
        backend_type: OAuth2BackendEnum,
        redirect_uri: str,
        authorization_response: str,
    ) -> str | None:
        backend = self.get_backend(backend_type)
        if backend is None:
            return None
        return await backend.get_user_email_from_provider(redirect_uri, authorization_response)
