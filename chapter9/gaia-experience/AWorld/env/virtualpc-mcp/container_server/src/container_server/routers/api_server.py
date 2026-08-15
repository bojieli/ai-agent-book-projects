import logging
from fastapi import APIRouter, Request

from .. import container_server_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/container/create")
async def create_container(request: Request, body: dict):
    token = body.get("token")
    logger.info(f"Create container: token={token}")
    container_id, ip_addr, mcp_port, novnc_port = (
        await container_server_manager.create_mcp_server_container()
    )
    logger.info(
        f"Container created: container_id={container_id}, ip_addr={ip_addr}, mcp_port={mcp_port}, novnc_port={novnc_port}"
    )

    return {
        "status": "success",
        "message": f"MCP server created: {ip_addr}:{mcp_port}",
        "data": {
            "ip_addr": ip_addr,
            "mcp_port": mcp_port,
            "novnc_port": novnc_port,
            "container_id": container_id,
        },
    }


@router.post("/container/shutdown")
async def shutdown_container(request: Request, body: dict):
    token = body.get("token")
    container_id = body.get("container_id")
    logger.info(f"Shutdown container: token={token}, container_id={container_id}")
    await container_server_manager.shutdown_mcp_server_container(container_id)
    logger.info(f"Container shutdown: container_id={container_id}")

    return {
        "status": "success",
        "message": f"MCP server shutdown: {container_id}",
    }
