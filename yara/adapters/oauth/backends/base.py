import abc

from yara.settings import YaraSettings


class OAuth2Backend:
    settings: YaraSettings

    def __init__(
        self,
        settings: YaraSettings,
    ) -> None:
        self.settings = settings

    @abc.abstractmethod
    async def get_authorization_url(
        self,
        redirect_uri: str,
    ) -> str | None:
        ...

    @abc.abstractmethod
    async def get_user_email_from_provider(
        self,
        redirect_uri: str,
        authorization_response: str,
    ) -> str | None:
        ...
