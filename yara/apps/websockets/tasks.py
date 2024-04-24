import logging

import orjson

from yara.core.tasks import celery_task

logger = logging.getLogger(__name__)


@celery_task
async def task_handle_ws_message(user_id: str, message_json: str) -> None:
    # from yara.main import root_app

    try:
        message = orjson.loads(message_json)
        logger.warning("message_json: user_id: %s, message_json: %s", user_id, message)
    except orjson.JSONDecodeError:
        logger.error("Error decoding message from JSON: %s", message_json)
