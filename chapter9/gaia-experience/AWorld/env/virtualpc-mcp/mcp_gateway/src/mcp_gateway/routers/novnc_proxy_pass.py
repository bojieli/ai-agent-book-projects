import asyncio
import logging
import websockets
from fastapi import APIRouter, Request, HTTPException, Response, WebSocket

from ..configs import vnc_auth

from ..sessions.session_connection import SessionId

from ..auth import check_auth
from ..utils.common_utils import get_remote_addr

logger = logging.getLogger(__name__)


router = APIRouter()


@router.api_route(
    "/{mcp_session_id}/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def novnc_proxy(request: Request, mcp_session_id: str):
    """
    Proxy for the VNC server.
    """
    # Auth check
    if vnc_auth and not check_auth.check_auth(request):
        logger.warning(
            f"Request unauthorized! remote.addr={get_remote_addr(request)}, request.headers={request.headers}"
        )
        return Response(status_code=401, content="Unauthorized")

    gateway = request.app.state.gateway
    session_connection = await gateway.session_connection_manager.get_session(
        SessionId(mcp_session_id=mcp_session_id)
    )

    if not session_connection:
        logger.warning(
            f"Session is invalid or expired: remote.addr={get_remote_addr(request)}, request.headers={request.headers}, session_id={mcp_session_id}"
        )
        raise HTTPException(status_code=400, detail="Session is invalid or expired")
    return await session_connection.novnc_proxy(request)


@router.websocket("/{mcp_session_id}/websockify")
async def websocket_novnc_proxy(websocket: WebSocket, mcp_session_id: str):
    """WebSocket proxy for noVNC websockify connections"""
    await websocket.accept()

    # Auth check
    if vnc_auth and not check_auth.get_auth_payload(dict(websocket.headers)):
        logger.warning(
            f"Request unauthorized! request.url={websocket.url}, request.headers={websocket.headers}"
        )
        await websocket.close(code=4000, reason="Unauthorized")
        return

    # Get session connection
    gateway = websocket.app.state.gateway
    session_connection = await gateway.session_connection_manager.get_session(
        SessionId(mcp_session_id=mcp_session_id)
    )
    if not session_connection:
        logger.warning(
            f"WebSocket: Session invalid or expired: session_id={mcp_session_id}"
        )
        await websocket.close(code=4000, reason="Session invalid or expired")
        return

    # Proxy WebSocket to backend container
    backend_ws_url = f"ws://{session_connection.container_ip_addr}:{session_connection.novnc_port}/websockify"
    logger.info(f"WebSocket: Proxying to {backend_ws_url}")

    async def _proxy_websocket(client_ws, backend_ws):
        """Simple bidirectional WebSocket proxy"""

        async def client_to_backend():
            while True:
                try:
                    message = await client_ws.receive_bytes()
                except:
                    try:
                        message = await client_ws.receive_text()
                    except:
                        break
                await backend_ws.send(message)

        async def backend_to_client():
            async for message in backend_ws:
                if isinstance(message, bytes):
                    await client_ws.send_bytes(message)
                else:
                    await client_ws.send_text(message)

        await asyncio.gather(
            client_to_backend(), backend_to_client(), return_exceptions=True
        )

    try:
        async with websockets.connect(backend_ws_url) as backend_ws:
            await _proxy_websocket(websocket, backend_ws)
    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
