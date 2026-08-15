from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import logging

from .configs import container_server_port
from .routers import api_server
from . import container_server_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events"""
    # Startup
    await container_server_manager.wait_docker_ready()
    await container_server_manager.load_mcp_server_image()
    await container_server_manager.start_mcp_server_life_cycle_manager()
    await container_server_manager.start_container_server_register_task()
    try:
        yield
    finally:
        # Shutdown
        # await mcp_server_manager.clean_mcp_server_container()
        pass


# FastAPI application setup with lifespan
app = FastAPI(
    title="MCP Container Server",
    description="MCP Container Server",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(api_server.router, prefix="/api")


@app.get("/health")
async def health(request: Request):
    return {"status": "success", "message": "Container server is healthy"}


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=container_server_port)
