import base64
import json
import logging

import aiohttp
from oauthlib.oauth2 import WebApplicationClient

from yara.adapters.oauth.backends.base import OAuth2Backend
from yara.settings import YaraSettings

logger = logging.getLogger(__name__)


class GoogleOAuth2Backend(OAuth2Backend):
    client: WebApplicationClient

    def __init__(
        self,
        settings: YaraSettings,
    ) -> None:
        super().__init__(settings)
        self.client = WebApplicationClient(settings.YARA_OAUTH2_GOOGLE_CLIENT_ID)

    async def get_authorization_url(
        self,
        redirect_uri: str,
    ) -> str | None:
        uri = "https://accounts.google.com/o/oauth2/auth"
        if not uri:
            return None
        return self.client.prepare_request_uri(
            uri,
            redirect_uri=redirect_uri,
            scope=["openid", "email"],
        )

    async def get_user_email_from_provider(
        self,
        redirect_uri: str,
        authorization_response: str,
    ) -> str | None:
        uri = "https://accounts.google.com/o/oauth2/token"
        code = self.client.parse_request_uri_response(authorization_response)["code"]
        token_url, headers, body = self.client.prepare_token_request(
            uri,
            authorization_response=authorization_response,
            redirect_url=redirect_uri,
            code=code,
        )
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                token_url,
                headers=headers,
                data=body,
                auth=aiohttp.BasicAuth(
                    self.settings.YARA_OAUTH2_GOOGLE_CLIENT_ID,
                    self.settings.YARA_OAUTH2_GOOGLE_CLIENT_SECRET,
                ),
            ) as token_response,
        ):
            token_data = await token_response.json()
            id_token = token_data.get("id_token")
            if not id_token:
                return None
            # Decode and parse the id_token to get the email
            id_token_payload = id_token.split(".")[1]
            id_token_payload_decoded = base64.urlsafe_b64decode(id_token_payload + "==").decode("utf-8")
            id_token_data = json.loads(id_token_payload_decoded)
            email = id_token_data["email"]  # Get the user's email address
            return email
