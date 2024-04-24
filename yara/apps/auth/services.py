import logging
import typing as tp
import uuid

from yara.adapters.oauth.adapter import OAuth2Adapter
from yara.adapters.orm.adapter import ORMAdapter, where_clause
from yara.apps.auth.helpers import (
    decode_jwt_token,
    encode_jwt_token,
    generate_random_string,
    hash_password,
    validate_password,
)
from yara.apps.auth.models import Group, User
from yara.apps.auth.schemas import (
    ResetPasswordCompletePayload,
    ResetPasswordPayload,
    ResetPasswordResponse,
    SignInMagicLinkCompletePayload,
    SignInMagicLinkPayload,
    SignInMagicLinkResponse,
    SignInOAuth2CallbackPayload,
    SignInOAuth2Payload,
    SignInOAuth2Response,
    SignInPayload,
    SignInResponse,
    SignUpCompletePayload,
    SignUpPayload,
    SignUpResponse,
)
from yara.apps.auth.tasks import task_send_email
from yara.core.services import YaraService
from yara.main import YaraRootApp

logger = logging.getLogger(__name__)


class AuthService(YaraService):
    secret_key: str
    access_token_expired_at: int
    refresh_token_expired_at: int
    magic_link_verification_token_exp_at: int
    sign_up_invitation_token_exp_at: int
    sign_up_verification_token_exp_at: int
    reset_password_verification_token_exp_at: int

    user_orm_adapter: ORMAdapter[User]
    group_orm_adapter: ORMAdapter[Group]

    def __init__(self, root_app: YaraRootApp) -> None:
        super().__init__(root_app)
        self.user_orm_adapter: ORMAdapter[User] = self.root_app.get_adapter(ORMAdapter)
        self.group_orm_adapter: ORMAdapter[Group] = self.root_app.get_adapter(ORMAdapter)
        self.oauth2_adapter: OAuth2Adapter = self.root_app.get_adapter(OAuth2Adapter)
        for setting, field, required in (
            ("YARA_AUTH_SECRET_KEY", "secret_key", True),
            ("YARA_AUTH_EXP_ACCESS_TOKEN", "access_token_expired_at", True),
            ("YARA_AUTH_EXP_REFRESH_TOKEN", "refresh_token_expired_at", True),
            ("YARA_AUTH_EXP_MAGIC_VERIFICATION_TOKEN", "magic_link_verification_token_exp_at", True),
            ("YARA_AUTH_EXP_SIGNUP_INVITATION_TOKEN", "sign_up_invitation_token_exp_at", True),
            ("YARA_AUTH_EXP_SIGNUP_VERIFICATION_TOKEN", "sign_up_verification_token_exp_at", True),
            ("YARA_AUTH_EXP_RESET_PASSWORD_VERIFICATION_TOKEN", "reset_password_verification_token_exp_at", True),
        ):
            value: tp.Any | None = getattr(root_app.settings, setting, None)
            if not value and required:
                raise ValueError(f"Provide {setting} settings")
            setattr(self, field, value)

    def generate_tokens(self, authenticated_user_id: uuid.UUID) -> SignInResponse:
        salt = generate_random_string()
        payload = {"id": str(authenticated_user_id), "salt": salt}
        access_token = encode_jwt_token(payload, self.access_token_expired_at, self.secret_key)
        refresh_token = encode_jwt_token(payload, self.refresh_token_expired_at, self.secret_key)
        return SignInResponse(access_token=access_token, refresh_token=refresh_token)

    def get_invitation_token(self, inviter_user_id: uuid.UUID, group_id: uuid.UUID) -> str | None:
        return encode_jwt_token(
            {
                "group_id": str(group_id),
                "inviter_user_id": str(inviter_user_id),
                "tags": ["sign-up-invitation"],
                "salt": generate_random_string(),
            },
            self.sign_up_invitation_token_exp_at,
            self.secret_key,
        )

    async def sign_in(self, payload: SignInPayload) -> SignInResponse:
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

    async def sign_in_magic_link(self, payload: SignInMagicLinkPayload) -> SignInMagicLinkResponse:
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
            self.magic_link_verification_token_exp_at,
            self.secret_key,
        )

        task_send_email.delay(
            to=payload.email,
            template_id="magic_link",
            payload={
                "magic_link": f"{payload.frontend_link}?magic_link_verification_token={magic_link_verification_token}",
            },
        )
        return SignInMagicLinkResponse(email=payload.email)

    async def sign_in_magic_link_complete(self, payload: SignInMagicLinkCompletePayload) -> SignInResponse:
        jwt_payload = decode_jwt_token(
            payload.magic_link_verification_token,
            self.secret_key,
        )
        if not jwt_payload or "magic-link" not in jwt_payload.get("tags", []):
            raise ValueError({"token": "Invalid magic link token"})
        user_id = jwt_payload.get("user_id")
        if not user_id or not await self.user_orm_adapter.exists(User, where_clause(id=user_id, is_active=True)):
            raise ValueError({"token": "Invalid magic link token"})

        return self.generate_tokens(uuid.UUID(user_id))

    async def sign_in_oauth2(self, payload: SignInOAuth2Payload) -> SignInOAuth2Response:
        authorization_url = await self.oauth2_adapter.get_authorization_url(
            payload.backend,
            payload.redirect_uri,
        )
        if not authorization_url:
            raise ValueError({"provider": "Not supported or configured provider"})
        return SignInOAuth2Response(authorization_url=authorization_url)

    async def sign_in_oauth2_callback(self, payload: SignInOAuth2CallbackPayload) -> SignInResponse:
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

    async def sign_up_invitation(self, inviter_user_id: uuid.UUID) -> str | None:
        user = await self.user_orm_adapter.read(
            User,
            where_clause(
                id=str(inviter_user_id),
                is_active=True,
                is_group_moderator=True,
            ),
        )
        if not user or not user.group_id:
            return None

        return self.get_invitation_token(inviter_user_id, user.group_id)

    async def sign_up(self, payload: SignUpPayload) -> SignUpResponse:
        if await self.user_orm_adapter.exists(User, where_clause(email=payload.email, is_active=True)):
            raise ValueError({"email": "Active user with the email already exists"})

        group_id = None
        if payload.invitation_token:
            jwt_payload = decode_jwt_token(
                payload.invitation_token,
                self.secret_key,
            )
            if not jwt_payload or "sign-up-invitation" not in jwt_payload.get("tags", []):
                raise ValueError({"token": "Invalid invitation token"})
            group_id = jwt_payload.get("group_id")

        update_or_create_payload = {
            "email": payload.email,
            "password": hash_password(payload.password),
            "is_active": False,
            "is_superuser": False,
            "is_group_moderator": False,
            "group_id": group_id,
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
            self.sign_up_verification_token_exp_at,
            self.secret_key,
        )

        task_send_email.delay(
            to=payload.email,
            template_id="sign_up",
            payload={
                "sign_up_link": f"{payload.frontend_link}?sign_up_verification_token={sign_up_verification_token}",
            },
        )
        return SignUpResponse(email=payload.email)

    async def sign_up_complete(self, payload: SignUpCompletePayload) -> SignInResponse:
        jwt_payload = decode_jwt_token(
            payload.sign_up_verification_token,
            self.secret_key,
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
        payload: ResetPasswordPayload,
    ) -> ResetPasswordResponse:
        user = await self.user_orm_adapter.read(User, where_clause(email=payload.email, is_active=True))
        if not user:
            return ResetPasswordResponse(email=payload.email)

        reset_password_verification_token = encode_jwt_token(
            {
                "user_id": str(user.id),
                "tags": ["reset-password"],
                "salt": generate_random_string(),
            },
            self.reset_password_verification_token_exp_at,
            self.secret_key,
        )

        task_send_email.delay(
            to=payload.email,
            template_id="reset_password",
            payload={
                "reset_password_link": f"{payload.frontend_link}?reset_password_verification_token={reset_password_verification_token}",
            },
        )
        return ResetPasswordResponse(email=payload.email)

    async def reset_password_complete(
        self,
        payload: ResetPasswordCompletePayload,
    ) -> SignInResponse:
        jwt_payload = decode_jwt_token(
            payload.reset_password_verification_token,
            self.secret_key,
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
        group_name: str | None = None,
        is_active: bool = True,
        is_group_moderator: bool = False,
        is_superuser: bool = False,
    ) -> None:
        group = await self.group_orm_adapter.read_or_create(
            Group,
            {
                "name": group_name,
            },
            where_clause(name=group_name),
        )
        await self.user_orm_adapter.update_or_create(
            User,
            {
                "email": email,
                "password": hash_password(password),
                "is_active": is_active,
                "is_superuser": is_superuser,
                "is_group_moderator": is_group_moderator,
                "group_id": group.id,
            },
            where_clause(email=email),
        )

    async def is_superuser(self, user_id: uuid.UUID) -> bool:
        return await self.user_orm_adapter.exists(User, where_clause(id=str(user_id), is_superuser=True))

    async def is_group_moderator(self, user_id: uuid.UUID) -> bool:
        return await self.user_orm_adapter.exists(User, where_clause(id=str(user_id), is_group_moderator=True))

    async def is_active(self, user_id: uuid.UUID) -> bool:
        return await self.user_orm_adapter.exists(User, where_clause(id=str(user_id), is_active=True))
