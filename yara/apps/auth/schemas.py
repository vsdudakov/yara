import enum

from pydantic import BaseModel, field_validator, model_validator

from yara.adapters.oauth.adapter import OAuth2BackendEnum


class ELanguage(enum.StrEnum):
    en = "en"
    es = "es"
    ru = "ru"


class SignInPayload(BaseModel):
    email: str
    password: str


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str


class SignInMagicLinkPayload(BaseModel):
    email: str
    frontend_link: str
    frontend_language: ELanguage | None = ELanguage.en


class SignInMagicLinkResponse(BaseModel):
    email: str


class SignInMagicLinkCompletePayload(BaseModel):
    magic_link_verification_token: str


class SignInOAuth2Payload(BaseModel):
    backend: OAuth2BackendEnum
    redirect_uri: str


class SignInOAuth2Response(BaseModel):
    authorization_url: str


class SignInOAuth2CallbackPayload(BaseModel):
    backend: OAuth2BackendEnum
    redirect_uri: str
    authorization_response: str


class SignUpPayload(BaseModel):
    email: str
    password: str
    repeat_password: str
    accept_terms_and_policies: bool

    invitation_token: str | None = None

    frontend_link: str
    frontend_language: ELanguage | None = ELanguage.en

    @field_validator("accept_terms_and_policies")
    @classmethod
    def accept_terms_and_policies_true(cls, accept_terms_and_policies: bool) -> bool:
        if not accept_terms_and_policies:
            raise ValueError("Terms and conditions acceptance required.")
        return accept_terms_and_policies

    @model_validator(mode="after")
    def check_passwords_match(self) -> "SignUpPayload":
        pw1 = self.password
        pw2 = self.repeat_password
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Passwords do not match")
        return self


class SignUpResponse(BaseModel):
    email: str


class SignUpCompletePayload(BaseModel):
    sign_up_verification_token: str


class ResetPasswordPayload(BaseModel):
    email: str
    frontend_link: str
    frontend_language: ELanguage | None = ELanguage.en


class ResetPasswordResponse(BaseModel):
    email: str


class ResetPasswordCompletePayload(BaseModel):
    reset_password_verification_token: str
    password: str
    repeat_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> "ResetPasswordCompletePayload":
        pw1 = self.password
        pw2 = self.repeat_password
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Passwords do not match")
        return self
