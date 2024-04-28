from uuid import UUID

from yara.apps.auth.routers import get_authenticated_user_id
from yara.apps.websockets.services import WebsocketService
from yara.core.routers import Depends, WebSocket, YaraApiRouter, get_service

router = YaraApiRouter(
    prefix="/websockets",
    tags=["websockets"],
)


@router.websocket("")
async def websockets(
    websocket: WebSocket,
    authenticated_user_id: UUID = Depends(get_authenticated_user_id),
    websockets_service: WebsocketService = Depends(get_service(WebsocketService)),
) -> None:
    await websockets_service.accept(
        authenticated_user_id,
        websocket,
    )
    await websockets_service.listen(
        authenticated_user_id,
        websocket,
    )
    await websockets_service.close_ws(
        authenticated_user_id,
        websocket,
    )
