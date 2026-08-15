"""
Event Server - FastAPI version with native async support for MCP tools
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from agent import EventTriggeredAgent, SystemHintConfig, resolve_provider_and_key
from event_types import Event, EventType
import threading
import time
import asyncio
import uvicorn


def _env_int(name: str, default: int) -> int:
    """Read an integer env var; fall back to default (with a warning) if malformed."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(f"Invalid {name} value: {raw!r} (must be an integer); using default {default}")
        return default


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global agent instance
agent: Optional[EventTriggeredAgent] = None
agent_lock = threading.Lock()

# Monitoring state
monitoring_enabled = False
monitoring_thread: Optional[threading.Thread] = None

# MCP loading status
mcp_loading_status = {
    "loading": False,
    "loaded": False,
    "tools_count": 0,
    "error": None,
    "started_at": None,
    "completed_at": None
}


# ============================================================================
# FastAPI Lifecycle Events (Modern lifespan)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global agent, monitoring_enabled
    
    # Startup
    logger.info("🚀 Starting Event-Triggered Agent Server (FastAPI)")
    await init_agent()
    logger.info("✅ Server ready to receive events\n")
    
    yield
    
    # Shutdown
    logger.info("Shutting down server...")
    monitoring_enabled = False
    
    if agent and agent.mcp_manager:
        await agent.mcp_manager.disconnect_all()
    
    logger.info("✅ Server shutdown complete")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Event-Triggered Agent Server",
    description="AI Agent with async MCP tools support",
    version="2.0.0",
    lifespan=lifespan
)


# Pydantic models for requests
class EventRequest(BaseModel):
    event_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ProcessRegister(BaseModel):
    process_id: str
    process_name: str
    metadata: Optional[Dict[str, Any]] = None


class ProcessUnregister(BaseModel):
    process_id: str


# ============================================================================
# Initialization
# ============================================================================

async def init_agent():
    """Initialize the agent with optional MCP tools"""
    global agent, mcp_loading_status
    
    # Determine provider and key, applying the universal OpenRouter fallback.
    requested_provider = os.getenv("LLM_PROVIDER", "kimi").lower()
    provider, api_key = resolve_provider_and_key(requested_provider)
    
    if not api_key:
        raise ValueError(
            f"API key not set for provider '{requested_provider}'. Set the appropriate "
            "environment variable or OPENROUTER_API_KEY."
        )
    
    # Get model from environment if specified
    model = os.getenv("LLM_MODEL")
    if provider == "openrouter" and provider != requested_provider and model and "/" not in model:
        model = None
    
    # Check if MCP should be enabled (default: true)
    enable_mcp = os.getenv("ENABLE_MCP_TOOLS", "true").lower() not in ["false", "0", "no"]
    
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True,
        save_trajectory=True,
        trajectory_file="event_agent_trajectory.json",
        temperature=_reasoning_safe_temperature(model, 0.7),
        max_tokens=4096,
        use_mcp_servers=enable_mcp
    )
    
    agent = EventTriggeredAgent(
        api_key=api_key,
        provider=provider,
        model=model,
        config=config,
        verbose=True
    )
    
    logger.info(f"✅ Agent initialized with {provider} provider")
    
    if enable_mcp:
        logger.info("🔄 MCP tools enabled (default) - loading asynchronously...")
        await load_mcp_tools_async()
    else:
        logger.info(f"📦 Using built-in tools only (MCP disabled via ENABLE_MCP_TOOLS=false)")


async def load_mcp_tools_async():
    """Load MCP tools asynchronously"""
    global agent, mcp_loading_status
    
    mcp_loading_status["loading"] = True
    mcp_loading_status["started_at"] = datetime.now().isoformat()
    
    try:
        if agent:
            await agent.load_mcp_tools()
            tools_count = len(agent.mcp_manager.tools)
            
            mcp_loading_status["loaded"] = True
            mcp_loading_status["loading"] = False
            mcp_loading_status["tools_count"] = tools_count
            mcp_loading_status["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"✅ MCP tools loaded: {tools_count} tools available")
            if tools_count > 0:
                sample_tools = list(agent.mcp_manager.tools.keys())[:5]
                logger.info(f"   Sample: {sample_tools}")
        else:
            raise RuntimeError("Agent not initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to load MCP tools: {e}")
        mcp_loading_status["loading"] = False
        mcp_loading_status["loaded"] = False
        mcp_loading_status["error"] = str(e)
        mcp_loading_status["completed_at"] = datetime.now().isoformat()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Event-Triggered Agent Server",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "event": "POST /event",
            "mcp_status": "GET /mcp/status",
            "mcp_reload": "POST /mcp/reload",
            "agent_status": "GET /agent/status",
            "agent_reset": "POST /agent/reset"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "monitoring_enabled": monitoring_enabled,
        "mcp_enabled": agent.config.use_mcp_servers if agent else False,
        "mcp_loaded": mcp_loading_status["loaded"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/mcp/status")
async def get_mcp_status():
    """Get MCP tools loading status"""
    status = mcp_loading_status.copy()
    
    # Add tool list if loaded
    if status["loaded"] and agent:
        status["tools"] = list(agent.mcp_manager.tools.keys())
        
        # Group by server
        status["tools_by_server"] = {}
        for tool_name in agent.mcp_manager.tools.keys():
            server = tool_name.split("_")[0]
            if server not in status["tools_by_server"]:
                status["tools_by_server"][server] = []
            status["tools_by_server"][server].append(tool_name)
    
    return status


@app.post("/mcp/reload")
async def reload_mcp_tools(background_tasks: BackgroundTasks):
    """Manually trigger MCP tools reload"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    if mcp_loading_status["loading"]:
        raise HTTPException(status_code=409, detail="MCP tools are already loading")
    
    # Use FastAPI background tasks
    background_tasks.add_task(load_mcp_tools_async)
    
    return {
        "success": True,
        "message": "MCP tools reload started in background"
    }


@app.post("/event")
async def handle_event(event_req: EventRequest):
    """Handle incoming event"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Create event
        event_data = {
            "event_type": event_req.event_type,
            "content": event_req.content,
            "metadata": event_req.metadata or {}
        }
        event = Event.from_dict(event_data)
        
        # Handle the event
        with agent_lock:
            result = agent.handle_event(event, max_iterations=20)
        
        return {
            "success": True,
            "event_id": event.event_id,
            "result": {
                "final_answer": result.get('final_answer'),
                "iterations": result.get('iterations'),
                "tool_calls_count": len(result.get('tool_calls') or []),
                "todo_items": len(result.get('todo_list') or []),
                "success": result.get('success', False),
                "trajectory_file": result.get('trajectory_file')
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/status")
async def get_agent_status():
    """Get current agent status"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    with agent_lock:
        return {
            "provider": agent.provider,
            "model": agent.model,
            "tool_calls_count": len(agent.tool_calls),
            "todo_items": len(agent.todo_list),
            "current_directory": agent.current_directory,
            "mcp_tools_loaded": agent.mcp_tools_loaded,
            "mcp_tools_count": len(agent.mcp_manager.tools) if agent.mcp_tools_loaded else 0
        }


@app.post("/agent/reset")
async def reset_agent():
    """Reset agent state"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    with agent_lock:
        agent.reset()
    
    return {
        "success": True,
        "message": "Agent state reset successfully"
    }


@app.post("/process/register")
async def register_process(process: ProcessRegister):
    """Register a background process for monitoring"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    with agent_lock:
        agent.background_processes[process.process_id] = {
            "name": process.process_name,
            "start_time": datetime.now().isoformat(),
            "metadata": process.metadata or {},
            "reminded": False
        }
    
    return {
        "success": True,
        "message": f"Process '{process.process_name}' registered"
    }


@app.post("/process/unregister")
async def unregister_process(process: ProcessUnregister):
    """Unregister a background process"""
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    with agent_lock:
        if process.process_id in agent.background_processes:
            del agent.background_processes[process.process_id]
            return {
                "success": True,
                "message": f"Process {process.process_id} unregistered"
            }
        else:
            return {
                "success": False,
                "message": f"Process {process.process_id} not found"
            }


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("🤖 EVENT-TRIGGERED AGENT SERVER (FastAPI)")
    print("="*80)
    print()
    
    # Get port from environment
    port = _env_int('AGENT_PORT', 8000)
    
    print(f"✅ Starting server on port {port}")
    print(f"📡 API Documentation: http://localhost:{port}/docs")
    print(f"📊 ReDoc: http://localhost:{port}/redoc")
    print()
    print("="*80 + "\n")
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
