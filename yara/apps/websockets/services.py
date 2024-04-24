import asyncio
import logging
import typing as tp
from collections.abc import AsyncIterator, Sequence
from uuid import UUID

import orjson

from yara.adapters.memory.adapter import MemoryAdapter
from yara.core.services import YaraService
from yara.main import YaraRootApp

logger = logging.getLogger(__name__)


class WebSocket(tp.Protocol):
    async def accept(self) -> None:
        ...

    def iter_text(self) -> AsyncIterator[str]:
        ...

    async def send_text(self, message: str) -> None:
        ...

    async def close(self) -> None:
        ...


class WebsocketService(YaraService):
    memory_set_subscribers_key: str = "ws_subscribers"
    memory_queue_messages_key: str = "ws_messages_for_{user_id}"
    task_handle_ws_message: tp.Any

    memory_adapter: MemoryAdapter

    def __init__(
        self,
        root_app: YaraRootApp,
        task_handle_ws_message: tp.Any,
    ) -> None:
        super().__init__(root_app)
        self.memory_adapter: MemoryAdapter = self.root_app.get_adapter(MemoryAdapter)
        self.task_handle_ws_message = task_handle_ws_message

    async def accept(
        self,
        user_id: UUID,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        await self.memory_adapter.sadd(self.memory_set_subscribers_key, str(user_id))

    async def _send_to_user(
        self,
        user_id: UUID | str,
        message_json: str | bytes,
        check_user: bool = True,
    ) -> bool:
        if check_user and not await self.memory_adapter.sismember(
            self.memory_set_subscribers_key,
            str(user_id),
        ):
            logger.warning("User %s is not a subscriber", user_id)
            return False
        await self.memory_adapter.lpush(
            self.memory_queue_messages_key.format(user_id=user_id),
            message_json,
        )
        return True

    async def send_to(
        self,
        user_ids: Sequence[UUID | str],
        message: dict[str, tp.Any],
    ) -> None:
        try:
            message_json = orjson.dumps(message)
        except orjson.JSONEncodeError:
            logger.error("Error encoding message to JSON: %s", message)
            return
        await asyncio.gather(
            *[
                self._send_to_user(
                    user_id,
                    message_json,
                )
                for user_id in user_ids
            ]
        )

    async def broadcast(
        self,
        message: dict[str, tp.Any],
    ) -> None:
        try:
            message_json = orjson.dumps(message)
        except orjson.JSONEncodeError:
            logger.error("Error encoding message to JSON: %s", message)
            return
        subscriber_ids = await self.memory_adapter.smembers(self.memory_set_subscribers_key)
        user_ids = [bytes(subscriber_id).decode("utf-8") for subscriber_id in subscriber_ids]  # type: ignore [arg-type]
        await asyncio.gather(
            *[
                self._send_to_user(
                    user_id,
                    message_json,
                    check_user=False,
                )
                for user_id in user_ids
            ]
        )

    async def _ws_receiver(self, user_id: UUID, websocket: WebSocket) -> None:
        async for message_json in websocket.iter_text():
            self.task_handle_ws_message.delay(str(user_id), message_json)

    async def _ws_sender(self, user_id: UUID, websocket: WebSocket) -> None:
        while True:
            _, message = await self.memory_adapter.brpop([self.memory_queue_messages_key.format(user_id=user_id)])
            message_str = bytes(message).decode("utf-8")  # type: ignore [arg-type]
            await websocket.send_text(message_str)

    async def listen(self, user_id: UUID, websocket: WebSocket) -> None:
        task_group: list[asyncio.Task[None]] = []

        async def run_ws_receiver() -> None:
            await self._ws_receiver(user_id, websocket)
            # Cancel all tasks in the task group when this task is done
            for task in task_group:
                task.cancel()

        receiver_task = asyncio.create_task(run_ws_receiver())
        task_group.append(receiver_task)

        sender_task = asyncio.create_task(self._ws_sender(user_id, websocket))
        task_group.append(sender_task)

        # Wait for all tasks in the task group to complete
        await asyncio.gather(*task_group)

    async def close_ws(self, user_id: UUID, websocket: WebSocket) -> None:
        await self.memory_adapter.srem(
            self.memory_set_subscribers_key,
            str(user_id),
        )
        await self.memory_adapter.delete(self.memory_queue_messages_key.format(user_id=user_id))
        await websocket.close()
