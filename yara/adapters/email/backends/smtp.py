import logging
import typing as tp
from email.message import EmailMessage

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from yara.adapters.email.backends.base import EmailBackend
from yara.settings import YaraSettings

logger = logging.getLogger(__name__)


class SmtpEmailBackend(EmailBackend):
    templates: dict[str, str]
    smtp_from: str
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    smtp_username: str
    smtp_password: str
    timeout: int | None = None

    def __init__(
        self,
        settings: YaraSettings,
    ) -> None:
        super().__init__(settings)
        for setting, field, required in (
            ("YARA_EMAIL_TEMPLATES", "templates", True),
            ("YARA_EMAIL_SMTP_FROM", "smtp_from", True),
            ("YARA_EMAIL_SMTP_HOST", "smtp_host", True),
            ("YARA_EMAIL_SMTP_PORT", "smtp_port", True),
            ("YARA_EMAIL_SMTP_USERNAME", "smtp_username", True),
            ("YARA_EMAIL_SMTP_PASSWORD", "smtp_password", True),
            ("YARA_EMAIL_SMTP_USE_TLS", "smtp_use_tls", True),
            ("YARA_EMAIL_TIMEOUT", "smtp_timeout", False),
        ):
            value: tp.Any | None = getattr(settings, setting, None)
            if value is None and required:
                raise ValueError(f"Provide {setting} settings")
            setattr(self, field, value)

    async def up(self) -> None:
        pass

    async def healthcheck(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass

    async def _send(self, message: EmailMessage) -> None:
        await aiosmtplib.send(
            message,
            hostname=self.smtp_host,
            port=self.smtp_port,
            timeout=self.timeout,
            use_tls=self.smtp_use_tls,
            username=self.smtp_username,
            password=self.smtp_password,
        )

    async def send_email(self, to: str, template_id: str, payload: dict[str, tp.Any]) -> None:
        template_path = self.templates.get(template_id)
        if not template_path:
            raise ValueError(f"Template {template_id} not found")
        templates_env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=select_autoescape(),
            enable_async=True,
        )

        subject_template = templates_env.get_template("subject.jinja")
        body_template = templates_env.get_template("body.jinja")

        subject = await subject_template.render_async(**payload)
        body = await body_template.render_async(**payload)

        message = EmailMessage()
        message["From"] = self.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message["Content-Type"] = "text/html; charset=utf-8"
        message.set_payload(body, "utf-8")

        await self._send(message)

        logger.info("Sending email to %s", to)
