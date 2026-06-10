from contextlib import asynccontextmanager
import logging
import os
import re
from typing import Optional

import boto3
import httpx
from botocore.auth import SigV4Auth as BotocoreSigV4Auth
from botocore.awsrequest import AWSRequest
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.environ.get("McpServerGatewayUrl", "").strip()
MCP_REQUIRE_IAM = os.environ.get("MCP_REQUIRE_IAM", "true").strip().lower() == "true"
MCP_TIMEOUT_SECONDS = int(os.environ.get("MCP_TIMEOUT_SECONDS", "15"))
MCP_SSE_READ_TIMEOUT_SECONDS = int(os.environ.get("MCP_SSE_READ_TIMEOUT_SECONDS", "300"))

_mcp_client: Optional["StrandsGatewayMcpClient"] = None


def _resolve_region() -> str:
    """Resolve the AWS region for MCP endpoint SigV4 signing."""
    explicit_region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or ""
    ).strip()
    if explicit_region:
        return explicit_region

    if MCP_SERVER_URL:
        patterns = [r"bedrock-agentcore\.([a-z0-9-]+)\.amazonaws\.com"]
        for pattern in patterns:
            match = re.search(pattern, MCP_SERVER_URL)
            if match:
                return match.group(1)

    session = boto3.Session()
    return session.region_name or "us-east-1"


def _resolve_frozen_credentials():
    """Resolve AWS credentials required for IAM SigV4 signing."""
    session = boto3.Session(region_name=_resolve_region())
    creds = session.get_credentials()
    if not creds:
        return None
    return creds.get_frozen_credentials()


def _resolve_service() -> str:
    """Resolve the AWS service name for SigV4 signing."""
    explicit_service = os.environ.get("MCP_AWS_SERVICE", "").strip()
    if explicit_service:
        return explicit_service

    return "bedrock-agentcore"


class AwsSigV4Auth(httpx.Auth):
    """Sign outgoing AgentCore Gateway requests with AWS SigV4.

    The robotics MCP gateway in this repo is created with
    GatewayAuthorizer.usingAwsIam(), so inbound gateway calls must be signed
    with the bedrock-agentcore service name.
    """

    requires_request_body = True

    def auth_flow(self, request: httpx.Request):
        credentials = _resolve_frozen_credentials()
        aws_region = _resolve_region()
        if MCP_REQUIRE_IAM and not credentials:
            raise RuntimeError(
                "IAM is required for MCP, but AWS credentials are unavailable."
            )
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
        BotocoreSigV4Auth(credentials, _resolve_service(), aws_region).add_auth(
            aws_request
        )

        for header_name, header_value in dict(aws_request.headers).items():
            request.headers[header_name] = header_value

        yield request


class StrandsGatewayMcpClient:
    """Gateway-backed Strands MCP client wrapper used by the speech agent.

    This keeps the native Strands MCP transport while supplying the IAM auth
    required by the gateway's AWS_IAM inbound authorizer.
    """

    def __init__(self, server_url: str):
        self.server_url = server_url
        self._client = MCPClient(
            self._create_transport,
            startup_timeout=max(MCP_TIMEOUT_SECONDS, 30),
        )

    @asynccontextmanager
    async def _create_transport(self):
        timeout = httpx.Timeout(
            MCP_TIMEOUT_SECONDS,
            read=MCP_SSE_READ_TIMEOUT_SECONDS,
        )
        logger.info(
            "Opening MCP transport. url=%s region=%s service=%s timeout=%s read_timeout=%s iam_required=%s",
            self.server_url,
            _resolve_region(),
            _resolve_service(),
            MCP_TIMEOUT_SECONDS,
            MCP_SSE_READ_TIMEOUT_SECONDS,
            MCP_REQUIRE_IAM,
        )
        async with httpx.AsyncClient(
            auth=AwsSigV4Auth(),
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            async with streamable_http_client(
                self.server_url,
                http_client=client,
            ) as streams:
                logger.info("MCP transport established for %s", self.server_url)
                yield streams
        logger.info("MCP transport closed for %s", self.server_url)

    def start(self) -> "StrandsGatewayMcpClient":
        logger.info("Starting MCP client for %s", self.server_url)
        try:
            self._client.start()
        except Exception:
            logger.exception("Failed to start MCP client for %s", self.server_url)
            raise
        logger.info("MCP client started for %s", self.server_url)
        return self

    def stop(self) -> None:
        logger.info("Stopping MCP client for %s", self.server_url)
        self._client.stop(None, None, None)
        logger.info("MCP client stopped for %s", self.server_url)

    def list_tools_sync(self, pagination_token: str | None = None, tool_filters: dict | None = None):
        logger.info(
            "Listing MCP tools. url=%s pagination_token=%s has_filters=%s",
            self.server_url,
            pagination_token,
            bool(tool_filters),
        )
        try:
            tools = self._client.list_tools_sync(
                pagination_token=pagination_token,
                tool_filters=tool_filters,
            )
        except Exception:
            logger.exception(
                "MCP tool listing failed. url=%s pagination_token=%s",
                self.server_url,
                pagination_token,
            )
            raise
        logger.info(
            "Listed MCP tools page. url=%s count=%s next_pagination_token=%s",
            self.server_url,
            len(tools),
            getattr(tools, "pagination_token", None),
        )
        return tools

    def call_tool_sync(self, tool_use_id: str, name: str, arguments: dict):
        logger.info(
            "Calling MCP tool. url=%s tool_use_id=%s name=%s argument_keys=%s",
            self.server_url,
            tool_use_id,
            name,
            sorted(arguments.keys()),
        )
        try:
            result = self._client.call_tool_sync(
                tool_use_id=tool_use_id,
                name=name,
                arguments=arguments,
            )
        except Exception:
            logger.exception(
                "MCP tool call failed. url=%s tool_use_id=%s name=%s",
                self.server_url,
                tool_use_id,
                name,
            )
            raise
        logger.info(
            "MCP tool call completed. url=%s tool_use_id=%s name=%s",
            self.server_url,
            tool_use_id,
            name,
        )
        return result


def get_mcp_client() -> StrandsGatewayMcpClient:
    """Return a native Strands MCP client for the configured AgentCore Gateway."""
    global _mcp_client

    if not MCP_SERVER_URL:
        raise ValueError("MCP endpoint is not configured. Set McpServerGatewayUrl.")

    if _mcp_client is None:
        logger.info(
            "Creating shared MCP client. url=%s region=%s service=%s",
            MCP_SERVER_URL,
            _resolve_region(),
            _resolve_service(),
        )
        _mcp_client = StrandsGatewayMcpClient(MCP_SERVER_URL).start()
        logger.info(
            "Connected to MCP server through native Strands MCPClient at %s using SigV4 service %s.",
            MCP_SERVER_URL,
            _resolve_service(),
        )

    return _mcp_client


def cleanup_mcp_client() -> None:
    """Close the shared MCP client session."""
    global _mcp_client

    if _mcp_client is None:
        return

    try:
        _mcp_client.stop()
    finally:
        _mcp_client = None
