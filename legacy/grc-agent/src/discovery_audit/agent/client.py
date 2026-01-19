"""
Agent Client
HTTP client for communicating with the central server
"""

import asyncio
import json
from typing import Optional, Any
from datetime import datetime
import aiohttp
from rich.console import Console

from ..platform.detector import PlatformDetector
from ..core.models import AuditResult


console = Console()


class AgentClient:
    """
    Agent client for communicating with the central server
    """

    def __init__(
        self,
        server_url: str,
        api_key: Optional[str] = None,
        agent_id: Optional[str] = None,
        verify_ssl: bool = True,
    ):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id
        self.verify_ssl = verify_ssl
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            ssl_context = None if self.verify_ssl else False

            self._session = aiohttp.ClientSession(
                headers=headers,
                connector=aiohttp.TCPConnector(ssl=ssl_context),
            )

        return self._session

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def register(self) -> str:
        """
        Register this agent with the server

        Returns:
            Agent ID assigned by the server
        """
        platform_info = PlatformDetector.detect_local()

        registration_data = {
            "hostname": platform_info.hostname,
            "ip_address": "0.0.0.0",  # Will be determined by server
            "os_type": platform_info.os_type.value,
            "os_version": platform_info.os_version,
            "agent_version": "0.1.0",
            "capabilities": self._get_capabilities(platform_info),
        }

        session = await self._get_session()

        try:
            async with session.post(
                f"{self.server_url}/api/v1/agents/register",
                json=registration_data,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.agent_id = data["agent_id"]
                    console.print(f"[green]Registered with server. Agent ID: {self.agent_id}[/]")
                    return self.agent_id
                else:
                    error = await response.text()
                    raise Exception(f"Registration failed: {error}")

        except aiohttp.ClientError as e:
            raise Exception(f"Connection to server failed: {e}")

    def _get_capabilities(self, platform_info) -> list[str]:
        """Determine agent capabilities based on platform"""
        capabilities = ["network_scan", "vulnerability_scan"]

        if platform_info.os_type.value == "windows":
            capabilities.extend(["windows_audit", "registry_audit"])
            if platform_info.is_domain_joined:
                capabilities.append("ad_audit")
        elif platform_info.os_type.value == "linux":
            capabilities.extend(["linux_audit", "pam_audit"])

        if platform_info.is_elevated:
            capabilities.append("privileged")

        return capabilities

    async def heartbeat(self) -> dict:
        """
        Send heartbeat to server

        Returns:
            Server response with pending tasks count
        """
        if not self.agent_id:
            raise Exception("Agent not registered")

        session = await self._get_session()

        try:
            async with session.post(
                f"{self.server_url}/api/v1/agents/{self.agent_id}/heartbeat",
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    # Agent not found, need to re-register
                    console.print("[yellow]Agent not found on server. Re-registering...[/]")
                    await self.register()
                    return {"status": "re-registered", "pending_tasks": 0}
                else:
                    error = await response.text()
                    raise Exception(f"Heartbeat failed: {error}")

        except aiohttp.ClientError as e:
            raise Exception(f"Connection to server failed: {e}")

    async def get_pending_tasks(self) -> list[dict]:
        """
        Get pending tasks for this agent

        Returns:
            List of pending task objects
        """
        if not self.agent_id:
            raise Exception("Agent not registered")

        session = await self._get_session()

        try:
            async with session.get(
                f"{self.server_url}/api/v1/agents/{self.agent_id}/tasks",
                params={"status": "pending"},
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get tasks: {error}")

        except aiohttp.ClientError as e:
            raise Exception(f"Connection to server failed: {e}")

    async def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status on server

        Args:
            task_id: Task ID
            status: New status (running, completed, failed)

        Returns:
            True if successful
        """
        session = await self._get_session()

        try:
            async with session.put(
                f"{self.server_url}/api/v1/tasks/{task_id}/status",
                params={"status": status},
            ) as response:
                return response.status == 200

        except aiohttp.ClientError as e:
            console.print(f"[yellow]Failed to update task status: {e}[/]")
            return False

    async def submit_results(
        self,
        task_id: str,
        result: AuditResult,
    ) -> bool:
        """
        Submit scan results to server

        Args:
            task_id: Task ID
            result: Audit result object

        Returns:
            True if successful
        """
        if not self.agent_id:
            raise Exception("Agent not registered")

        session = await self._get_session()

        result_data = {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "result_data": result.model_dump(mode='json'),
            "findings_count": len(result.findings),
            "critical_count": result.score.critical_count if result.score else 0,
            "high_count": result.score.high_count if result.score else 0,
            "medium_count": result.score.medium_count if result.score else 0,
            "low_count": result.score.low_count if result.score else 0,
            "score": result.score.overall_score if result.score else 0,
            "grade": result.score.grade if result.score else "N/A",
        }

        try:
            async with session.post(
                f"{self.server_url}/api/v1/results",
                json=result_data,
            ) as response:
                if response.status == 200:
                    console.print("[green]Results submitted to server[/]")
                    return True
                else:
                    error = await response.text()
                    console.print(f"[red]Failed to submit results: {error}[/]")
                    return False

        except aiohttp.ClientError as e:
            console.print(f"[red]Connection to server failed: {e}[/]")
            return False

    async def check_server_health(self) -> bool:
        """
        Check if server is reachable

        Returns:
            True if server is healthy
        """
        session = await self._get_session()

        try:
            async with session.get(
                f"{self.server_url}/api/v1/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                return response.status == 200

        except Exception:
            return False
