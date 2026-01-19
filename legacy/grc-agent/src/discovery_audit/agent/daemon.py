"""
Agent Daemon
Background service that connects to server, receives tasks, and executes audits
"""

import asyncio
import signal
import sys
from typing import Optional
from datetime import datetime
from rich.console import Console

from .client import AgentClient
from ..core.engine import DiscoveryEngine
from ..core.models import AuditConfig


console = Console()


class AgentDaemon:
    """
    Agent daemon that runs in the background
    - Connects to central server
    - Sends periodic heartbeats
    - Receives and executes scan tasks
    - Reports results back to server
    """

    def __init__(
        self,
        server_url: str,
        api_key: Optional[str] = None,
        heartbeat_interval: int = 30,
        verify_ssl: bool = True,
    ):
        self.server_url = server_url
        self.api_key = api_key
        self.heartbeat_interval = heartbeat_interval
        self.verify_ssl = verify_ssl

        self.client: Optional[AgentClient] = None
        self.running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._task_check_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the agent daemon"""
        console.print("[bold blue]Starting GRC Agent Daemon[/]")

        # Initialize client
        self.client = AgentClient(
            server_url=self.server_url,
            api_key=self.api_key,
            verify_ssl=self.verify_ssl,
        )

        # Check server connectivity
        console.print(f"[dim]Connecting to server: {self.server_url}[/]")

        if not await self.client.check_server_health():
            console.print("[red]Cannot reach server. Will retry...[/]")
            await self._wait_for_server()

        # Register with server
        try:
            await self.client.register()
        except Exception as e:
            console.print(f"[red]Registration failed: {e}[/]")
            return

        self.running = True

        # Set up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop())
            )

        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._task_check_task = asyncio.create_task(self._task_check_loop())

        console.print("[green]Agent daemon started[/]")

        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Stop the agent daemon"""
        console.print("[yellow]Stopping agent daemon...[/]")
        self.running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self._task_check_task:
            self._task_check_task.cancel()

        if self.client:
            await self.client.close()

        console.print("[green]Agent daemon stopped[/]")

    async def _wait_for_server(self):
        """Wait for server to become available"""
        retry_interval = 10
        max_interval = 300  # 5 minutes max

        while not await self.client.check_server_health():
            console.print(f"[dim]Server not available. Retrying in {retry_interval}s...[/]")
            await asyncio.sleep(retry_interval)
            retry_interval = min(retry_interval * 2, max_interval)

        console.print("[green]Server connection established[/]")

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to server"""
        while self.running:
            try:
                response = await self.client.heartbeat()

                if response.get("pending_tasks", 0) > 0:
                    console.print(f"[cyan]{response['pending_tasks']} pending tasks available[/]")

            except Exception as e:
                console.print(f"[yellow]Heartbeat failed: {e}[/]")
                # Try to reconnect
                await asyncio.sleep(5)
                if not await self.client.check_server_health():
                    await self._wait_for_server()
                    try:
                        await self.client.register()
                    except Exception:
                        pass

            await asyncio.sleep(self.heartbeat_interval)

    async def _task_check_loop(self):
        """Check for and execute pending tasks"""
        while self.running:
            try:
                tasks = await self.client.get_pending_tasks()

                for task in tasks:
                    if not self.running:
                        break

                    await self._execute_task(task)

            except Exception as e:
                console.print(f"[yellow]Task check failed: {e}[/]")

            await asyncio.sleep(10)  # Check every 10 seconds

    async def _execute_task(self, task: dict):
        """Execute a scan task"""
        task_id = task.get("id")
        task_type = task.get("task_type", "full")
        targets = task.get("targets", [])
        options = task.get("options", {})

        console.print(f"[bold]Executing task {task_id[:8]}... ({task_type})[/]")

        # Update task status to running
        await self.client.update_task_status(task_id, "running")

        try:
            # Build audit config based on task type
            config = self._build_config(task_type, options)

            # Run the audit
            engine = DiscoveryEngine(config)

            if not targets:
                targets = ["localhost"]

            result = await engine.run_audit(targets)

            # Submit results
            await self.client.submit_results(task_id, result)

            # Update task status
            await self.client.update_task_status(task_id, "completed")

            console.print(f"[green]Task {task_id[:8]} completed[/]")

        except Exception as e:
            console.print(f"[red]Task {task_id[:8]} failed: {e}[/]")
            await self.client.update_task_status(task_id, "failed")

    def _build_config(self, task_type: str, options: dict) -> AuditConfig:
        """Build audit config based on task type"""
        config = AuditConfig(
            name=f"Remote Audit - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            output_dir="./reports",
        )

        if task_type == "quick":
            config.enable_vuln_scan = False
            config.enable_web_audit = False
            config.scan_ports = "22,80,443,445,3389"

        elif task_type == "network":
            config.enable_system_audit = False
            config.enable_web_audit = False
            config.enable_vuln_scan = True

        elif task_type == "system":
            config.enable_network_scan = False
            config.enable_web_audit = False
            config.enable_vuln_scan = False

        elif task_type == "ad":
            config.enable_network_scan = False
            config.enable_web_audit = False
            config.enable_vuln_scan = False
            # AD audit will be triggered by system audit

        elif task_type == "compliance":
            config.enable_network_scan = False
            config.enable_web_audit = False
            config.enable_vuln_scan = False

        # Apply custom options
        for key, value in options.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config


async def run_daemon_async(
    server_url: str,
    api_key: Optional[str] = None,
    heartbeat_interval: int = 30,
    verify_ssl: bool = True,
):
    """Run the agent daemon (async)"""
    daemon = AgentDaemon(
        server_url=server_url,
        api_key=api_key,
        heartbeat_interval=heartbeat_interval,
        verify_ssl=verify_ssl,
    )

    await daemon.start()


def run_daemon():
    """CLI entry point for da-agent command"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="GRC Security Audit Agent")
    parser.add_argument("--server", required=True, help="Server URL (e.g., https://server:8080)")
    parser.add_argument("--api-key", default=os.getenv("GRC_API_KEY"), help="API key for authentication")
    parser.add_argument("--heartbeat", type=int, default=30, help="Heartbeat interval in seconds")
    parser.add_argument("--no-ssl-verify", action="store_true", help="Disable SSL verification")

    args = parser.parse_args()

    asyncio.run(run_daemon_async(
        server_url=args.server,
        api_key=args.api_key,
        heartbeat_interval=args.heartbeat,
        verify_ssl=not args.no_ssl_verify,
    ))


if __name__ == "__main__":
    run_daemon()
