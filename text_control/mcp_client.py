"""
MCP Client module - Handles MCP client initialization and management with
AWS SigV4 authentication using native Strands MCP client
"""

import asyncio
from contextlib import asynccontextmanager
import logging
import os
import re
import uuid
from typing import Any, Dict, Optional, Set

import boto3
import httpx
from botocore.auth import SigV4Auth as BotocoreSigV4Auth
from botocore.awsrequest import AWSRequest
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp.mcp_client import MCPClient

from config import MCP_SERVER_URL

logger = logging.getLogger(__name__)

# Global MCP client instance
_mcp_client: Optional["SecureMCPClient"] = None


def _resolve_region(mcp_url: str) -> str:
    """Resolve the AWS region for MCP endpoint SigV4 signing."""
    explicit_region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or ""
    ).strip()
    if explicit_region:
        return explicit_region

    if mcp_url:
        patterns = [r"bedrock-agentcore\.([a-z0-9-]+)\.amazonaws\.com"]
        for pattern in patterns:
            match = re.search(pattern, mcp_url)
            if match:
                return match.group(1)

    session = boto3.Session()
    return session.region_name or "us-east-1"


def _resolve_frozen_credentials(mcp_url: str):
    """Resolve AWS credentials required for IAM SigV4 signing."""
    session = boto3.Session(region_name=_resolve_region(mcp_url))
    creds = session.get_credentials()
    if not creds:
        return None
    return creds.get_frozen_credentials()


def _resolve_service(mcp_url: str) -> str:
    """Resolve the AWS service name for SigV4 signing."""
    explicit_service = os.environ.get("MCP_AWS_SERVICE", "").strip()
    if explicit_service:
        return explicit_service

    if "bedrock-agentcore" in mcp_url:
        return "bedrock-agentcore"
    return "lambda"


class AwsSigV4Auth(httpx.Auth):
    """Sign outgoing AgentCore Gateway requests with AWS SigV4."""

    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url

    requires_request_body = True

    def auth_flow(self, request: httpx.Request):
        credentials = _resolve_frozen_credentials(self.mcp_url)
        aws_region = _resolve_region(self.mcp_url)
        service = _resolve_service(self.mcp_url)

        if not credentials:
            raise RuntimeError("Missing AWS credentials for MCP request signing.")

        headers = dict(request.headers)
        headers.pop("connection", None)

        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers,
        )
        BotocoreSigV4Auth(credentials, service, aws_region).add_auth(
            aws_request
        )

        for header_name, header_value in dict(aws_request.headers).items():
            request.headers[header_name] = header_value

        yield request


def _convert_tool_result_to_dict(result: Any) -> Dict[str, Any]:
    """Convert any tool call result to a standard dict expected by routes/api.py."""
    if isinstance(result, dict):
        return result

    # If it is a native CallToolResult object or has content attribute
    if hasattr(result, "content"):
        content_list = []
        for item in getattr(result, "content", []):
            if isinstance(item, dict):
                content_list.append(item)
            else:
                item_dict = {}
                if hasattr(item, "type"):
                    item_dict["type"] = item.type
                else:
                    item_dict["type"] = "text"

                if hasattr(item, "text"):
                    item_dict["text"] = item.text
                elif hasattr(item, "value"):
                    item_dict["text"] = item.value
                else:
                    item_dict["text"] = str(item)
                content_list.append(item_dict)
        return {
            "toolUseId": getattr(result, "toolUseId", "unknown"),
            "content": content_list,
            "isError": getattr(result, "isError", False),
        }

    # Fallback
    return {
        "content": [{"type": "text", "text": str(result)}]
    }


class SecureMCPClient:
    """MCP Client that uses the native Strands MCP client over AgentCore Gateway
    with AWS SigV4 authentication or standard HTTP requests."""

    def __init__(self, mcp_url: str, use_aws_auth: bool = True):
        self.mcp_url = mcp_url
        self.use_aws_auth = use_aws_auth
        self.timeout_seconds = int(os.environ.get("MCP_TIMEOUT_SECONDS", "15"))
        self.sse_read_timeout = int(os.environ.get("MCP_SSE_READ_TIMEOUT_SECONDS", "300"))

        print(f"Creating SecureMCPClient. url={self.mcp_url} use_aws_auth={self.use_aws_auth}")

        self._client = MCPClient(
            self._create_transport,
            startup_timeout=max(self.timeout_seconds, 30),
        )
        self.start()

    @asynccontextmanager
    async def _create_transport(self):
        timeout = httpx.Timeout(
            self.timeout_seconds,
            read=self.sse_read_timeout,
        )
        print(f"Opening MCP transport. url={self.mcp_url}")

        auth = None
        if self.use_aws_auth:
            auth = AwsSigV4Auth(self.mcp_url)

        async with httpx.AsyncClient(
            auth=auth,
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            async with streamable_http_client(
                self.mcp_url,
                http_client=client,
            ) as streams:
                print(f"MCP transport established for {self.mcp_url}")
                yield streams
        print(f"MCP transport closed for {self.mcp_url}")

    def start(self) -> "SecureMCPClient":
        """Start the MCP client background process."""
        print(f"Starting MCP client for {self.mcp_url}")
        try:
            self._client.start()
            print(f"MCP client started successfully for {self.mcp_url}")
        except Exception as e:
            print(f"Failed to start MCP client for {self.mcp_url}: {e}")
            raise
        return self

    async def _recreate_client(self):
        """Safely close and recreate the underlying MCP client on failure."""
        print(f"Recreating underlying MCP client for {self.mcp_url}...")
        try:
            self._client.stop(None, None, None)
        except Exception as e:
            print(f"Error stopping client during reset: {e}")
        
        self._client = MCPClient(
            self._create_transport,
            startup_timeout=max(self.timeout_seconds, 30),
        )
        self.start()

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any] = None
    ) -> Any:
        """Call a tool with AWS authentication"""
        arguments = arguments or {}
        tool_use_id = f"text-control-{uuid.uuid4()}"

        def _sync_call():
            return self._client.call_tool_sync(
                tool_use_id=tool_use_id,
                name=tool_name,
                arguments=arguments
            )

        try:
            result = await asyncio.to_thread(_sync_call)
            return _convert_tool_result_to_dict(result)
        except Exception as e:
            print(f"MCP tool call failed: {e}. Retrying with recreated client...")
            try:
                await self._recreate_client()
                result = await asyncio.to_thread(_sync_call)
                return _convert_tool_result_to_dict(result)
            except Exception as retry_e:
                raise MCPError(f"MCP tool call failed after retry: {retry_e}") from retry_e

    async def list_tools(self) -> list:
        """List available tools"""
        def _sync_list():
            tools = []
            pagination_token = None
            while True:
                paginated_tools = self._client.list_tools_sync(
                    pagination_token=pagination_token
                )
                page_tools = list(paginated_tools)
                tools.extend(page_tools)
                pagination_token = getattr(paginated_tools, "pagination_token", None)
                if pagination_token is None:
                    break
            return tools

        try:
            tools = await asyncio.to_thread(_sync_list)
        except Exception as e:
            print(f"MCP list tools failed: {e}. Retrying with recreated client...")
            try:
                await self._recreate_client()
                tools = await asyncio.to_thread(_sync_list)
            except Exception as retry_e:
                raise MCPError(f"MCP list tools failed after retry: {retry_e}") from retry_e

        # Ensure every tool has the tool_name and description attributes expected by models/actions.py
        for tool in tools:
            if not hasattr(tool, "tool_name"):
                if hasattr(tool, "mcp_tool") and hasattr(tool.mcp_tool, "name"):
                    setattr(tool, "tool_name", tool.mcp_tool.name)
                elif hasattr(tool, "name"):
                    setattr(tool, "tool_name", tool.name)
            if not hasattr(tool, "description"):
                if hasattr(tool, "mcp_tool") and hasattr(tool.mcp_tool, "description"):
                    setattr(tool, "description", tool.mcp_tool.description)
                elif hasattr(tool, "_tool_spec") and isinstance(tool._tool_spec, dict):
                    setattr(tool, "description", tool._tool_spec.get("description", "No description"))
        
        return tools

    async def close(self):
        """Close the client and clean up resources"""
        print(f"Stopping MCP client for {self.mcp_url}")
        try:
            self._client.stop(None, None, None)
            print("MCP client stopped successfully")
        except Exception as e:
            print(f"Error stopping MCP client: {e}")

    async def __aenter__(self):
        """Async context manager entry - no-op to keep shared client alive"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - no-op to keep shared client alive"""
        pass


class MCPError(Exception):
    """Custom exception for MCP-related errors"""


_last_request_id: Optional[str] = None


def notify_new_invocation(request_id: str):
    """Notify the MCP client module of a new Lambda invocation request ID to proactively heal the connection."""
    global _last_request_id, _mcp_client
    if _last_request_id != request_id:
        print(f"New Lambda invocation detected. request_id={request_id}, previous={_last_request_id}")
        _last_request_id = request_id
        if _mcp_client is not None:
            print("Proactively closing stale MCP client from previous invocation to avoid freeze timeouts...")
            cleanup_mcp_client()


def get_mcp_client() -> SecureMCPClient:
    """Get MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        use_aws_auth = os.getenv("MCP_USE_AWS_AUTH", "true").lower() == "true"
        if not MCP_SERVER_URL:
            raise ValueError("MCP_SERVER_URL not configured")
        auth_type = 'AWS SigV4' if use_aws_auth else 'standard'
        print(f"Initializing MCP client with {auth_type} authentication. URL={MCP_SERVER_URL}")
        _mcp_client = SecureMCPClient(MCP_SERVER_URL, use_aws_auth=use_aws_auth)
    return _mcp_client


def cleanup_mcp_client():
    """Clean up MCP client"""
    global _mcp_client
    if _mcp_client is not None:
        try:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(_mcp_client.close())
                else:
                    loop.run_until_complete(_mcp_client.close())
            except RuntimeError:
                asyncio.run(_mcp_client.close())
        except Exception as e:
            print(f"Error closing MCP client: {e}")
        finally:
            _mcp_client = None
