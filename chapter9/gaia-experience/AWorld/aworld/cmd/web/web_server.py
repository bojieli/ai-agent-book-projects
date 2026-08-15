import asyncio
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
import uvicorn
import os
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from aworld.cmd.utils.agent_server import AgentServer
from aworld.cmd.utils.webui_builder import build_webui

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
async def root():
    return RedirectResponse("/index.html")

agent_server = AgentServer(
    server_id="default_server",
    server_name="default_server",
)

app.state.agent_server = agent_server

from .routers import chats, workspaces, sessions, traces  # noqa

app.include_router(chats.router, prefix=chats.prefix)
app.include_router(workspaces.router, prefix=workspaces.prefix)
app.include_router(sessions.router, prefix=sessions.prefix)
app.include_router(traces.router, prefix=traces.prefix)


static_path = build_webui(force_rebuild=os.getenv("AWORLD_WEB_UI_FORCE_REBUILD", False))
logger.info(f"Mounting static files from {static_path}")
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: int = 300):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            return Response("Request timeout", status_code=408)


app.add_middleware(TimeoutMiddleware, timeout=300)


def run_server(port, args=None, **kwargs):
    logger.info(f"Running Web server on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
