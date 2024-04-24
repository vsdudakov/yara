import logging
import typing as tp
from email.message import EmailMessage

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from yara.adapters.email.backends.base import EmailBackend

logger = logging.getLogger(__name__)


class SmtpEmailBackend(EmailBackend):
    async def up(self) -> None:
        pass

    async def healthcheck(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass

    async def _send(self, message: EmailMessage) -> None:
        await aiosmtplib.send(
            message,
            hostname=self.settings.YARA_EMAIL_SMTP_HOST,
            port=self.settings.YARA_EMAIL_SMTP_PORT,
            timeout=self.settings.YARA_EMAIL_SMTP_TIMEOUT,
            use_tls=self.settings.YARA_EMAIL_SMTP_USE_TLS,
            username=self.settings.YARA_EMAIL_SMTP_USERNAME,
            password=self.settings.YARA_EMAIL_SMTP_PASSWORD,
        )

    async def send_email(self, to: str, template_id: str, payload: dict[str, tp.Any]) -> None:
        template_path = self.settings.YARA_EMAIL_TEMPLATES.get(template_id)
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
        message["From"] = self.settings.YARA_EMAIL_SMTP_FROM
        message["To"] = to
        message["Subject"] = subject
        message["Content-Type"] = "text/html; charset=utf-8"
        message.set_payload(body, "utf-8")

        await self._send(message)

        logger.info("Sending email to %s", to)
