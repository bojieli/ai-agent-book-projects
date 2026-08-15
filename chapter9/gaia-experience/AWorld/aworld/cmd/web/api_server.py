import logging
from fastapi import FastAPI
import uvicorn

from aworld.cmd.utils.agent_server import AgentServer


logger = logging.getLogger(__name__)

app = FastAPI()

agent_server = AgentServer(
    server_id="default_server",
    server_name="default_server",
)

app.state.agent_server = agent_server

from .routers import chats, workspaces, sessions

app.include_router(chats.router, prefix=chats.prefix)
app.include_router(workspaces.router, prefix=workspaces.prefix)
app.include_router(sessions.router, prefix=sessions.prefix)


def run_server(port, args=None, **kwargs):
    logger.info(f"Running API server on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
