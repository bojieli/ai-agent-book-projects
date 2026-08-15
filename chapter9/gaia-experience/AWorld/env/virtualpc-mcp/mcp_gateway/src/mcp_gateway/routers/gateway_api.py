import logging
import traceback
from fastapi import APIRouter, Request
from ..utils.common_utils import get_remote_addr

router = APIRouter()

logger = logging.getLogger(__name__)

from ..containers import ContainerServer
from ..mcp_gateway import MCPGateway


@router.post("/container_server/register")
async def container_server_register(request: Request, body: dict):
    """Register a container server with deduplication"""
    try:
        gateway: MCPGateway = request.app.state.gateway
        new_server = ContainerServer(**body)
        await gateway.container_server_manager.register_container_server(new_server)
    except Exception as e:
        logger.error(
            f"Failed to register container server, remote.addr={get_remote_addr(request)}\n{traceback.format_exc()}"
        )
        return {"status": "error", "message": "Failed to register container server"}
