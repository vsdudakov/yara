import typing as tp
from uuid import UUID

from yara.apps.auth import schemas
from yara.apps.auth.helpers import get_authenticated_user_id, get_authenticated_user_id_from_refresh
from yara.apps.auth.services import AuthService
from yara.core.api_router import Depends, Response, YaraApiRouter, get_root_app

auth_router = YaraApiRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth_router.post("/sign-in")
async def sign_in(
    payload: schemas.SignInPayload,
    response: Response,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInResponse:
    """Sign in with email and password

    To access protected endpoints, you need to pass the access token in the `Authorization` header:

    `Authorization: Bearer <access_token>`

    HTTP only cookies are used for web to store the tokens. You don't need to send headers manually.
    """
    service = AuthService(root_app)
    tokens = await service.sign_in(payload)
    # for web
    response.set_cookie("access_token_cookie", value=tokens.access_token, httponly=True)
    response.set_cookie("refresh_token_cookie", value=tokens.refresh_token, httponly=True)
    # for mobile
    return tokens


@auth_router.post("/sign-in/magic-link")
async def sign_in_magic_link(
    payload: schemas.SignInMagicLinkPayload,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInMagicLinkResponse:
    """Sign in with magic link

    The process:
    - User enters email
    - The frontend sends POST to `/api/auth/sign-in/magic-link` with email
    - The backend generates a magic link verification token
    - The backend sends an email with the magic verification token
    - The user clicks on the link in the email
    - The frontend sends POST to `/api/auth/sign-in/magic-link/complete` with the magic verification token
    - The backend verifies the magic verification token and returns access and refresh tokens
    """
    service = AuthService(root_app)
    return await service.sign_in_magic_link(payload)


@auth_router.post("/sign-in/magic-link/complete")
async def sign_in_magic_link_complete(
    payload: schemas.SignInMagicLinkCompletePayload,
    response: Response,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInResponse:
    service = AuthService(root_app)
    tokens = await service.sign_in_magic_link_complete(payload)
    # for web
    response.set_cookie("access_token_cookie", value=tokens.access_token, httponly=True)
    response.set_cookie("refresh_token_cookie", value=tokens.refresh_token, httponly=True)
    # for mobile
    return tokens


@auth_router.post("/sign-in/oauth2")
async def sign_in_oauth2(
    payload: schemas.SignInOAuth2Payload,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInOAuth2Response:
    """Sign in with OAuth2 provider

    The process:

    - User clicks on the button "Sign in with Google"
    - The frontend sends POST to `/api/auth/sign-in/oauth2` with the provider name
    - The backend returns the authorization URL
    - The frontend redirects the user to the authorization URL
    - The user signs in with the provider and grants access to the app
    - The provider redirects the user to redirect url with the authorization code

    For web:
    - Web page sends the authorization code to the backend `/api/v1/auth/sign-in/oauth2/callback`
    - Backend provides the access token and refresh token

    For mobile:
    - Web page open mobile app with the authorization code
    - Mobile app sends the code to the backend `/api/v1/auth/sign-in/oauth2/callback`
    - Backend provides the access token and refresh token
    """
    service = AuthService(root_app)
    return await service.sign_in_oauth2(payload)


@auth_router.post("/sign-in/oauth2/callback")
async def sign_in_oauth2_callback(
    payload: schemas.SignInOAuth2CallbackPayload,
    response: Response,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInResponse:
    service = AuthService(root_app)
    tokens = await service.sign_in_oauth2_callback(payload)
    # for web
    response.set_cookie("access_token_cookie", value=tokens.access_token, httponly=True)
    response.set_cookie("refresh_token_cookie", value=tokens.refresh_token, httponly=True)
    # for mobile
    return tokens


@auth_router.post("/refresh-tokens")
async def refresh_tokens(
    response: Response,
    authenticated_user_id: UUID = Depends(get_authenticated_user_id_from_refresh),
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInResponse:
    """Refresh access and refresh tokens

    To refresh tokens, you need to pass the refresh token in the `Authorization` header:

    `Authorization: Bearer <refresh_token>`
    """
    service = AuthService(root_app)
    tokens = service.generate_tokens(authenticated_user_id)
    # for web
    response.set_cookie("access_token_cookie", value=tokens.access_token, httponly=True)
    response.set_cookie("refresh_token_cookie", value=tokens.refresh_token, httponly=True)
    # for mobile
    return tokens


@auth_router.get("/sign-up-invitation")
async def sign_up_invitation(
    root_app: tp.Any = Depends(get_root_app),
    authenticated_user_id: UUID = Depends(get_authenticated_user_id),
) -> str | None:
    """Sign up invitation

    The process:

    - Invitor user generates a sign up invitation link using this endpoint
    - Invitor user sends the invitation link to the user
    - The user starts the sign up process using the invitation link
    - The user will be added to the invitor user's group
    """
    service = AuthService(root_app)
    return await service.sign_up_invitation(authenticated_user_id)


@auth_router.post("/sign-up")
async def sign_up(
    payload: schemas.SignUpPayload,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignUpResponse:
    """Sign up

    The process:

    - User enters email and password
    - The frontend sends POST to `/api/auth/sign-up` with email and password
    - The backend creates a user with `is_active=False` and generates a sign up verification token
    - The backend sends an email with the sign up verification token
    - The user clicks on the link in the email
    - The frontend sends POST to `/api/auth/sign-up/complete` with the sign up verification token
    - The backend verifies the user and returns access and refresh tokens
    """
    service = AuthService(root_app)
    return await service.sign_up(payload)


@auth_router.post("/sign-up/complete")
async def sign_up_complete(
    response: Response,
    payload: schemas.SignUpCompletePayload,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInResponse:
    service = AuthService(root_app)
    tokens = await service.sign_up_complete(payload)
    # for web
    response.set_cookie("access_token_cookie", value=tokens.access_token, httponly=True)
    response.set_cookie("refresh_token_cookie", value=tokens.refresh_token, httponly=True)
    # for mobile
    return tokens


@auth_router.post("/reset-password")
async def reset_password(
    payload: schemas.ResetPasswordPayload,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.ResetPasswordResponse:
    """Reset password

    The process:

    - User enters email
    - The frontend sends POST to `/api/auth/reset-password` with email
    - The backend generates a reset password token
    - The backend sends an email with the reset password verification token
    - The user clicks on the link in the email
    - The frontend sends POST to `/api/auth/reset-password/complete` with the reset password verification token and new password
    - The backend verifies the reset password verification token and updates the password
    """
    service = AuthService(root_app)
    return await service.reset_password(payload)


@auth_router.post("/reset-password/complete")
async def reset_password_complete(
    response: Response,
    payload: schemas.ResetPasswordCompletePayload,
    root_app: tp.Any = Depends(get_root_app),
) -> schemas.SignInResponse:
    service = AuthService(root_app)
    tokens = await service.reset_password_complete(payload)
    # for web
    response.set_cookie("access_token_cookie", value=tokens.access_token, httponly=True)
    response.set_cookie("refresh_token_cookie", value=tokens.refresh_token, httponly=True)
    # for mobile
    return tokens


@auth_router.post("/sign-out")
async def sign_out(
    response: Response,
    root_app: tp.Any = Depends(get_root_app),
    authenticated_user_id: UUID = Depends(get_authenticated_user_id),
) -> None:
    service = AuthService(root_app)
    await service.sign_out(authenticated_user_id)
    # for web
    response.delete_cookie("access_token_cookie")
    response.delete_cookie("refresh_token_cookie")
    # for mobile nothing to do
    return