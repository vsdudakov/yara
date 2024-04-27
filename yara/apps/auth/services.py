import logging
import uuid

from yara.adapters.oauth.adapter import OAuth2Adapter
from yara.adapters.orm.adapter import ORMAdapter, where_clause
from yara.apps.auth import schemas
from yara.apps.auth.models import User
from yara.apps.auth.tasks import task_send_email
from yara.core.helpers import (
    decode_jwt_token,
    encode_jwt_token,
    generate_random_string,
    hash_password,
    validate_password,
)
from yara.core.services import YaraService
from yara.main import YaraRootApp

logger = logging.getLogger(__name__)


class AuthService(YaraService):
    user_orm_adapter: ORMAdapter[User]

    def __init__(self, root_app: YaraRootApp) -> None:
        super().__init__(root_app)
        self.user_orm_adapter: ORMAdapter[User] = self.root_app.get_adapter(ORMAdapter)
        self.oauth2_adapter: OAuth2Adapter = self.root_app.get_adapter(OAuth2Adapter)

    def generate_tokens(self, authenticated_user_id: uuid.UUID) -> schemas.SignInResponse:
        salt = generate_random_string()
        payload = {"id": str(authenticated_user_id), "salt": salt}
        access_token = encode_jwt_token(
            payload,
            self.root_app.settings.YARA_AUTH_EXP_ACCESS_TOKEN,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )
        refresh_token = encode_jwt_token(
            payload,
            self.root_app.settings.YARA_AUTH_EXP_REFRESH_TOKEN,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )
        return schemas.SignInResponse(access_token=access_token, refresh_token=refresh_token)

    async def sign_in(self, payload: schemas.SignInPayload) -> schemas.SignInResponse:
        user: User | None = await self.user_orm_adapter.read(
            User,
            where_clause(
                email=payload.email,
                is_active=True,
            ),
        )
        if not user or not validate_password(user.password, payload.password):
            raise ValueError(
                {
                    "email": "Active user with these credentials does not exist",
                    "password": "Active user with these credentials does not exist",
                }
            )

        return self.generate_tokens(user.id)

    async def sign_in_magic_link(self, payload: schemas.SignInMagicLinkPayload) -> schemas.SignInMagicLinkResponse:
        user: User | None = await self.user_orm_adapter.read(
            User,
            where_clause(email=payload.email, is_active=True),
        )
        if not user:
            raise ValueError({"email": "Active user with the email does not exist"})

        magic_link_verification_token = encode_jwt_token(
            {
                "user_id": str(user.id),
                "tags": ["magic-link"],
                "salt": generate_random_string(),
            },
            self.root_app.settings.YARA_AUTH_EXP_MAGIC_VERIFICATION_TOKEN,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )

        task_send_email.delay(
            to=payload.email,
            template_id=f"magic_link_{payload.frontend_locale}",
            payload={
                "magic_link": f"{payload.frontend_link}?magic_link_verification_token={magic_link_verification_token}",
            },
        )
        return schemas.SignInMagicLinkResponse(email=payload.email)

    async def sign_in_magic_link_complete(
        self, payload: schemas.SignInMagicLinkCompletePayload
    ) -> schemas.SignInResponse:
        jwt_payload = decode_jwt_token(
            payload.magic_link_verification_token,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )
        if not jwt_payload or "magic-link" not in jwt_payload.get("tags", []):
            raise ValueError({"token": "Invalid magic link token"})
        user_id = jwt_payload.get("user_id")
        if not user_id or not await self.user_orm_adapter.exists(User, where_clause(id=user_id, is_active=True)):
            raise ValueError({"token": "Invalid magic link token"})

        return self.generate_tokens(uuid.UUID(user_id))

    async def sign_in_oauth2(self, payload: schemas.SignInOAuth2Payload) -> schemas.SignInOAuth2Response:
        authorization_url = await self.oauth2_adapter.get_authorization_url(
            payload.backend,
            payload.redirect_uri,
        )
        if not authorization_url:
            raise ValueError({"provider": "Not supported or configured provider"})
        return schemas.SignInOAuth2Response(authorization_url=authorization_url)

    async def sign_in_oauth2_callback(self, payload: schemas.SignInOAuth2CallbackPayload) -> schemas.SignInResponse:
        user_email = await self.oauth2_adapter.get_user_email_from_provider(
            payload.backend,
            payload.redirect_uri,
            payload.authorization_response,
        )
        if not user_email:
            raise ValueError({"authorization_response": "Couldn't fetch user data using the authorization response."})

        user: User | None = await self.user_orm_adapter.read(
            User,
            where_clause(email=user_email),
        )
        if not user:
            raise ValueError({"authorization_response": "Couldn't fetch user data using the authorization response."})

        if not user.is_active:
            await self.user_orm_adapter.update(
                User,
                {"is_active": True},
                where_clause(email=user_email),
            )

        return self.generate_tokens(user.id)

    async def sign_up(self, payload: schemas.SignUpPayload) -> schemas.SignUpResponse:
        if await self.user_orm_adapter.exists(User, where_clause(email=payload.email, is_active=True)):
            raise ValueError({"email": "Active user with the email already exists"})

        update_or_create_payload = {
            "email": payload.email,
            "password": hash_password(payload.password),
            "is_active": False,
            "is_superuser": False,
        }
        user = await self.user_orm_adapter.update_or_create(
            User,
            update_or_create_payload,
            where_clause(email=payload.email),
        )
        sign_up_verification_token = encode_jwt_token(
            {
                "user_id": str(user.id),
                "tags": ["sign-up-verification"],
                "salt": generate_random_string(),
            },
            self.root_app.settings.YARA_AUTH_EXP_SIGNUP_VERIFICATION_TOKEN,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )

        task_send_email.delay(
            to=payload.email,
            template_id=f"sign_up_{payload.frontend_locale}",
            payload={
                "sign_up_link": f"{payload.frontend_link}?sign_up_verification_token={sign_up_verification_token}",
            },
        )
        return schemas.SignUpResponse(email=payload.email)

    async def sign_up_complete(self, payload: schemas.SignUpCompletePayload) -> schemas.SignInResponse:
        jwt_payload = decode_jwt_token(
            payload.sign_up_verification_token,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )
        if not jwt_payload or "sign-up-verification" not in jwt_payload.get("tags", []):
            raise ValueError({"token": "Invalid sign up verification token"})
        user_id = jwt_payload.get("user_id")
        if not user_id or not await self.user_orm_adapter.exists(User, where_clause(id=user_id, is_active=False)):
            raise ValueError({"token": "Invalid sign up verification token"})

        await self.user_orm_adapter.update(
            User,
            {"is_active": True},
            where_clause(id=jwt_payload["user_id"]),
        )

        return self.generate_tokens(uuid.UUID(user_id))

    async def reset_password(
        self,
        payload: schemas.ResetPasswordPayload,
    ) -> schemas.ResetPasswordResponse:
        user = await self.user_orm_adapter.read(User, where_clause(email=payload.email, is_active=True))
        if not user:
            return schemas.ResetPasswordResponse(email=payload.email)

        reset_password_verification_token = encode_jwt_token(
            {
                "user_id": str(user.id),
                "tags": ["reset-password"],
                "salt": generate_random_string(),
            },
            self.root_app.settings.YARA_AUTH_EXP_RESET_PASSWORD_VERIFICATION_TOKEN,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )

        task_send_email.delay(
            to=payload.email,
            template_id=f"reset_password_{payload.frontend_locale}",
            payload={
                "reset_password_link": f"{payload.frontend_link}?reset_password_verification_token={reset_password_verification_token}",
            },
        )
        return schemas.ResetPasswordResponse(email=payload.email)

    async def reset_password_complete(
        self,
        payload: schemas.ResetPasswordCompletePayload,
    ) -> schemas.SignInResponse:
        jwt_payload = decode_jwt_token(
            payload.reset_password_verification_token,
            self.root_app.settings.YARA_AUTH_SECRET_KEY,
        )
        if not jwt_payload or "reset-password" not in jwt_payload.get("tags", []):
            raise ValueError({"token": "Invalid reset password token"})
        user_id = jwt_payload.get("user_id")
        if not user_id or not await self.user_orm_adapter.exists(User, where_clause(id=user_id)):
            raise ValueError({"token": "Invalid reset password token"})

        update_payload = {
            "password": hash_password(payload.password),
        }
        await self.user_orm_adapter.update(
            User,
            update_payload,
            where_clause(id=user_id),
        )

        return self.generate_tokens(uuid.UUID(user_id))

    async def sign_out(self, authenticated_user_id: uuid.UUID) -> bool:
        return True

    async def create_user(
        self,
        email: str,
        password: str,
        is_active: bool = True,
        is_superuser: bool = False,
    ) -> None:
        await self.user_orm_adapter.update_or_create(
            User,
            {
                "email": email,
                "password": hash_password(password),
                "is_active": is_active,
                "is_superuser": is_superuser,
            },
            where_clause(email=email),
        )

    async def is_superuser(self, user_id: uuid.UUID) -> bool:
        return await self.user_orm_adapter.exists(User, where_clause(id=str(user_id), is_superuser=True))

    async def is_active(self, user_id: uuid.UUID) -> bool:
        return await self.user_orm_adapter.exists(User, where_clause(id=str(user_id), is_active=True))

    async def update_user(
        self,
        authenticated_user_id: uuid.UUID,
        payload: schemas.UserUpdatePayload,
    ) -> None:
        if payload.email and await self.user_orm_adapter.exists(User, where_clause(email=payload.email)):
            raise ValueError({"email": "User with this email already exists"})
        await self.user_orm_adapter.update(
            User,
            payload.model_dump(exclude_unset=True),
            where_clause(id=str(authenticated_user_id)),
        )

    async def change_password(
        self,
        authenticated_user_id: uuid.UUID,
        payload: schemas.UserChangePasswordPayload,
    ) -> None:
        user = await self.user_orm_adapter.read(User, where_clause(id=str(authenticated_user_id)))
        if not user or not validate_password(user.password, payload.old_password):
            raise ValueError({"old_password": "Old password is incorrect"})

        update_payload = {
            "password": hash_password(payload.new_password),
        }
        await self.user_orm_adapter.update(
            User,
            update_payload,
            where_clause(id=str(authenticated_user_id)),
        )

    async def get_me(
        self,
        authenticated_user_id: uuid.UUID,
    ) -> User | None:
        return await self.user_orm_adapter.read(User, where_clause(id=str(authenticated_user_id)))
