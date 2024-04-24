import logging
import typing as tp

from yara.adapters.email.adapter import EmailAdapter
from yara.core.tasks import celery_task

logger = logging.getLogger(__name__)


@celery_task
async def task_send_email(
    to: str,
    template_id: str,
    payload: dict[str, tp.Any],
) -> None:
    from yara.main import root_app

    email_adapter: EmailAdapter = root_app.get_adapter(EmailAdapter)
    await email_adapter.send_email(
        to,
        template_id,
        payload,
    )
