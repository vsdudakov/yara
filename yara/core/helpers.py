import logging
import typing as tp
from importlib import import_module

logger = logging.getLogger(__name__)


def import_obj(path: str) -> tp.Any | None:
    module, cls = path.rsplit(".", 1)
    try:
        command_module = import_module(module)
        return getattr(command_module, cls)
    except (ImportError, AttributeError) as e:
        logger.exception(e)
        return None
