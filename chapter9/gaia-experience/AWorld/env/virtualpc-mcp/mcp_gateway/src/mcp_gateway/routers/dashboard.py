import json
import logging
import traceback
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from ..utils.common_utils import get_remote_addr

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/status")
async def dashboard(request: Request):
    """Show dashboard"""
    try:
        gateway = request.app.state.gateway
        sessions = await gateway.session_connection_manager.get_sessions()
        container_servers = (
            await gateway.container_server_manager.get_container_servers()
        )
        status = {
            "status": "success",
            "data": {
                "sessions": [session.model_dump() for session in sessions],
                "container_servers": [
                    server.model_dump(exclude={"token"})
                    for server in container_servers
                ],
            },
        }
        return Response(
            content=json.dumps(status, ensure_ascii=False, indent=2).encode("utf-8"),
            status_code=200,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
    except Exception as e:
        logger.error(
            f"Failed to get dashboard, remote.addr={get_remote_addr(request)}\n{traceback.format_exc()}"
        )
        return JSONResponse(
            content={"status": "error", "message": "Failed to get dashboard"},
            status_code=500,
        )
