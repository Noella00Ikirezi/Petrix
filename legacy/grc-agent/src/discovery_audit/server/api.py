"""
REST API Server
Central server for managing agents and collecting results
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, Any
from contextlib import asynccontextmanager

from ..core.models import AuditResult
from .models import (
    ServerConfig,
    AgentRegistration,
    AgentInfo,
    AgentStatus,
    ScanTask,
    ScanResult,
)


# In-memory storage (replace with database in production)
agents: dict[str, AgentInfo] = {}
tasks: dict[str, ScanTask] = {}
results: dict[str, ScanResult] = {}


def create_app(config: Optional[ServerConfig] = None):
    """
    Create the FastAPI application

    Args:
        config: Server configuration

    Returns:
        FastAPI application instance
    """
    try:
        from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
    except ImportError:
        raise RuntimeError("FastAPI is required for the server component. Install with: pip install fastapi uvicorn")

    config = config or ServerConfig()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        print(f"Starting GRC Audit Server on {config.host}:{config.port}")
        # Start background task to check agent health
        task = asyncio.create_task(agent_health_check())
        yield
        # Shutdown
        task.cancel()
        print("Shutting down GRC Audit Server")

    app = FastAPI(
        title="GRC Security Audit Server",
        description="Central server for managing security audit agents",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Key verification
    async def verify_api_key(x_api_key: str = Header(None)):
        if config.api_key and x_api_key != config.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return x_api_key

    # Agent health check background task
    async def agent_health_check():
        while True:
            await asyncio.sleep(60)  # Check every minute
            now = datetime.now()
            for agent_id, agent in agents.items():
                if agent.status != AgentStatus.OFFLINE:
                    if (now - agent.last_seen).total_seconds() > 300:  # 5 minutes
                        agent.status = AgentStatus.OFFLINE

    # ===== Agent Endpoints =====

    @app.post("/api/v1/agents/register", response_model=dict)
    async def register_agent(
        registration: AgentRegistration,
        api_key: str = Depends(verify_api_key)
    ):
        """Register a new agent with the server"""
        agent_id = str(uuid.uuid4())

        agent = AgentInfo(
            id=agent_id,
            hostname=registration.hostname,
            ip_address=registration.ip_address,
            os_type=registration.os_type,
            os_version=registration.os_version,
            agent_version=registration.agent_version,
            capabilities=registration.capabilities,
            status=AgentStatus.ONLINE,
        )

        agents[agent_id] = agent

        return {
            "agent_id": agent_id,
            "message": "Agent registered successfully",
            "server_time": datetime.now().isoformat(),
        }

    @app.post("/api/v1/agents/{agent_id}/heartbeat")
    async def agent_heartbeat(
        agent_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Receive heartbeat from an agent"""
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent = agents[agent_id]
        agent.last_seen = datetime.now()

        if agent.status == AgentStatus.OFFLINE:
            agent.status = AgentStatus.ONLINE

        # Check for pending tasks
        pending_tasks = [
            t for t in tasks.values()
            if t.agent_id == agent_id and t.status == "pending"
        ]

        return {
            "status": "ok",
            "pending_tasks": len(pending_tasks),
            "server_time": datetime.now().isoformat(),
        }

    @app.get("/api/v1/agents", response_model=list[dict])
    async def list_agents(api_key: str = Depends(verify_api_key)):
        """List all registered agents"""
        return [agent.model_dump() for agent in agents.values()]

    @app.get("/api/v1/agents/{agent_id}")
    async def get_agent(
        agent_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Get agent details"""
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")

        return agents[agent_id].model_dump()

    @app.delete("/api/v1/agents/{agent_id}")
    async def delete_agent(
        agent_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Remove an agent"""
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")

        del agents[agent_id]
        return {"message": "Agent removed"}

    # ===== Task Endpoints =====

    @app.post("/api/v1/tasks")
    async def create_task(
        agent_id: str,
        task_type: str,
        targets: list[str] = None,
        options: dict = None,
        api_key: str = Depends(verify_api_key)
    ):
        """Create a new scan task for an agent"""
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")

        task_id = str(uuid.uuid4())

        task = ScanTask(
            id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            targets=targets or [],
            options=options or {},
        )

        tasks[task_id] = task

        return {
            "task_id": task_id,
            "message": "Task created",
        }

    @app.get("/api/v1/tasks/{task_id}")
    async def get_task(
        task_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Get task details"""
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        return tasks[task_id].model_dump()

    @app.get("/api/v1/agents/{agent_id}/tasks")
    async def get_agent_tasks(
        agent_id: str,
        status: str = None,
        api_key: str = Depends(verify_api_key)
    ):
        """Get tasks for an agent"""
        agent_tasks = [
            t.model_dump() for t in tasks.values()
            if t.agent_id == agent_id and (status is None or t.status == status)
        ]

        return agent_tasks

    @app.put("/api/v1/tasks/{task_id}/status")
    async def update_task_status(
        task_id: str,
        status: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Update task status"""
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        task = tasks[task_id]
        task.status = status

        if status == "running":
            task.started_at = datetime.now()
            agents[task.agent_id].status = AgentStatus.SCANNING
            agents[task.agent_id].current_task = task_id
        elif status in ["completed", "failed"]:
            task.completed_at = datetime.now()
            agents[task.agent_id].status = AgentStatus.ONLINE
            agents[task.agent_id].current_task = None

        return {"message": "Status updated"}

    # ===== Result Endpoints =====

    @app.post("/api/v1/results")
    async def submit_result(
        result: ScanResult,
        api_key: str = Depends(verify_api_key)
    ):
        """Submit scan results from an agent"""
        if result.task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        results[result.task_id] = result

        # Update task status
        task = tasks[result.task_id]
        task.status = "completed"
        task.completed_at = datetime.now()

        # Update agent status
        if result.agent_id in agents:
            agents[result.agent_id].status = AgentStatus.ONLINE
            agents[result.agent_id].current_task = None

        return {
            "message": "Results submitted",
            "result_id": result.task_id,
        }

    @app.get("/api/v1/results/{task_id}")
    async def get_result(
        task_id: str,
        api_key: str = Depends(verify_api_key)
    ):
        """Get scan results"""
        if task_id not in results:
            raise HTTPException(status_code=404, detail="Results not found")

        return results[task_id].model_dump()

    @app.get("/api/v1/results")
    async def list_results(
        limit: int = 50,
        api_key: str = Depends(verify_api_key)
    ):
        """List recent scan results"""
        sorted_results = sorted(
            results.values(),
            key=lambda r: r.completed_at,
            reverse=True
        )

        return [r.model_dump() for r in sorted_results[:limit]]

    # ===== Dashboard Endpoints =====

    @app.get("/api/v1/dashboard/summary")
    async def dashboard_summary(api_key: str = Depends(verify_api_key)):
        """Get dashboard summary"""
        online_agents = sum(1 for a in agents.values() if a.status == AgentStatus.ONLINE)
        scanning_agents = sum(1 for a in agents.values() if a.status == AgentStatus.SCANNING)

        recent_results = sorted(
            results.values(),
            key=lambda r: r.completed_at,
            reverse=True
        )[:10]

        total_criticals = sum(r.critical_count for r in results.values())
        total_highs = sum(r.high_count for r in results.values())

        return {
            "agents": {
                "total": len(agents),
                "online": online_agents,
                "scanning": scanning_agents,
                "offline": len(agents) - online_agents - scanning_agents,
            },
            "tasks": {
                "total": len(tasks),
                "pending": sum(1 for t in tasks.values() if t.status == "pending"),
                "running": sum(1 for t in tasks.values() if t.status == "running"),
                "completed": sum(1 for t in tasks.values() if t.status == "completed"),
            },
            "findings": {
                "total_critical": total_criticals,
                "total_high": total_highs,
            },
            "recent_scans": [
                {
                    "agent": agents.get(r.agent_id, {}).hostname if r.agent_id in agents else "Unknown",
                    "score": r.score,
                    "grade": r.grade,
                    "completed": r.completed_at.isoformat(),
                }
                for r in recent_results
            ],
        }

    @app.get("/api/v1/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agents_connected": sum(1 for a in agents.values() if a.status != AgentStatus.OFFLINE),
        }

    return app


def run_server(config: Optional[ServerConfig] = None):
    """Run the server"""
    try:
        import uvicorn
    except ImportError:
        raise RuntimeError("uvicorn is required to run the server. Install with: pip install uvicorn")

    config = config or ServerConfig()
    app = create_app(config)

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        ssl_keyfile=config.ssl_key,
        ssl_certfile=config.ssl_cert,
    )


def main():
    """CLI entry point for da-server command"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="GRC Security Audit Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--api-key", default=os.getenv("GRC_API_KEY"), help="API key for authentication")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate")
    parser.add_argument("--ssl-key", help="Path to SSL private key")

    args = parser.parse_args()

    config = ServerConfig(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        ssl_cert=args.ssl_cert,
        ssl_key=args.ssl_key,
    )

    run_server(config)


if __name__ == "__main__":
    main()
