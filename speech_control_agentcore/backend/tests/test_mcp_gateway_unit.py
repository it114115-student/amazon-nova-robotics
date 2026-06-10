#!/usr/bin/env python3
"""Unit tests for AgentCore Gateway MCP integration."""

import asyncio
import importlib
import os
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))


def _clear_imports():
    for module_name in [
        "tools",
        "tools.mcp_client",
        "tools.robot_actions",
        "strands",
        "strands.tools",
        "strands.tools.mcp",
        "strands.tools.mcp.mcp_client",
        "strands.tools.tools",
        "strands.types",
        "strands.types.tools",
        "strands.types._events",
        "mcp",
        "mcp.client",
        "mcp.client.streamable_http",
        "httpx",
        "boto3",
        "botocore",
        "botocore.auth",
        "botocore.awsrequest",
    ]:
        sys.modules.pop(module_name, None)


def _install_dependency_stubs():
    httpx_module = types.ModuleType("httpx")

    class FakeAuth:
        pass

    class FakeTimeout:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    class FakeRequest:
        def __init__(self):
            self.method = "POST"
            self.url = "https://example.com"
            self.content = b""
            self.headers = {}

    httpx_module.Auth = FakeAuth
    httpx_module.Request = FakeRequest
    httpx_module.Timeout = FakeTimeout
    httpx_module.AsyncClient = FakeAsyncClient
    sys.modules["httpx"] = httpx_module

    boto3_module = types.ModuleType("boto3")
    boto3_module.Session = MagicMock()
    sys.modules["boto3"] = boto3_module

    botocore_module = types.ModuleType("botocore")
    botocore_auth_module = types.ModuleType("botocore.auth")
    botocore_awsrequest_module = types.ModuleType("botocore.awsrequest")

    class FakeSigV4Auth:
        def __init__(self, *args, **kwargs):
            pass

        def add_auth(self, request):
            return request

    class FakeAWSRequest:
        def __init__(self, method=None, url=None, data=None, headers=None):
            self.method = method
            self.url = url
            self.data = data
            self.headers = headers or {}

    botocore_auth_module.SigV4Auth = FakeSigV4Auth
    botocore_awsrequest_module.AWSRequest = FakeAWSRequest
    sys.modules["botocore"] = botocore_module
    sys.modules["botocore.auth"] = botocore_auth_module
    sys.modules["botocore.awsrequest"] = botocore_awsrequest_module

    strands_module = types.ModuleType("strands")
    strands_tools_module = types.ModuleType("strands.tools")
    strands_tools_mcp_module = types.ModuleType("strands.tools.mcp")
    strands_tools_mcp_client_module = types.ModuleType("strands.tools.mcp.mcp_client")
    strands_tools_tools_module = types.ModuleType("strands.tools.tools")
    strands_types_module = types.ModuleType("strands.types")
    strands_types_tools_module = types.ModuleType("strands.types.tools")
    strands_types_events_module = types.ModuleType("strands.types._events")
    mcp_module = types.ModuleType("mcp")
    mcp_client_module = types.ModuleType("mcp.client")
    mcp_streamable_http_module = types.ModuleType("mcp.client.streamable_http")

    class FakePythonAgentTool:
        def __init__(self, tool_name, tool_spec, tool_func):
            self.tool_name = tool_name
            self.description = tool_spec.get("description")
            self._tool_spec = tool_spec
            self.tool_func = tool_func

    class FakeWrappedMCPAgentTool:
        pass

    class FakeAgentTool:
        def __init__(self):
            pass

    class FakeToolResultEvent(dict):
        def __init__(self, tool_result):
            super().__init__({"type": "tool_result", "tool_result": tool_result})

    class FakeMCPClient:
        def __init__(self, transport_callable, startup_timeout=30, **kwargs):
            self.transport_callable = transport_callable
            self.startup_timeout = startup_timeout
            self.kwargs = kwargs
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True
            return self

        def stop(self, exc_type=None, exc_val=None, exc_tb=None):
            self.stopped = True

        def list_tools_sync(self, pagination_token=None, tool_filters=None):
            return PaginatedTools([], None)

        def call_tool_sync(self, tool_use_id, name, arguments=None):
            return {
                "toolUseId": tool_use_id,
                "content": [{"text": f"{name}:{arguments or {}}"}],
            }

    def fake_streamable_http_client(*args, **kwargs):
        return SimpleNamespace(args=args, kwargs=kwargs)

    strands_tools_mcp_client_module.MCPClient = FakeMCPClient
    strands_tools_tools_module.PythonAgentTool = FakePythonAgentTool
    strands_types_tools_module.AgentTool = FakeAgentTool
    strands_types_tools_module.ToolGenerator = object
    strands_types_tools_module.ToolSpec = dict
    strands_types_tools_module.ToolUse = dict
    strands_types_events_module.ToolResultEvent = FakeToolResultEvent
    mcp_streamable_http_module.streamable_http_client = fake_streamable_http_client
    sys.modules["strands"] = strands_module
    sys.modules["strands.tools"] = strands_tools_module
    sys.modules["strands.tools.mcp"] = strands_tools_mcp_module
    sys.modules["strands.tools.mcp.mcp_client"] = strands_tools_mcp_client_module
    sys.modules["strands.tools.tools"] = strands_tools_tools_module
    sys.modules["strands.types"] = strands_types_module
    sys.modules["strands.types.tools"] = strands_types_tools_module
    sys.modules["strands.types._events"] = strands_types_events_module
    sys.modules["mcp"] = mcp_module
    sys.modules["mcp.client"] = mcp_client_module
    sys.modules["mcp.client.streamable_http"] = mcp_streamable_http_module


def _reload_module(module_name: str):
    _clear_imports()
    _install_dependency_stubs()
    return importlib.import_module(module_name)


class PaginatedTools(list):
    """Minimal paginated list shape compatible with the production code."""

    def __init__(self, items, token):
        super().__init__(items)
        self.pagination_token = token


class FakeTool:
    def __init__(self, name: str):
        self.mcp_tool = SimpleNamespace(name=name)
        self.mcp_client = MagicMock()
        self.tool_name = name


class TestMcpClient(unittest.TestCase):
    def test_get_mcp_client_requires_endpoint_url(self):
        with patch.dict(os.environ, {}, clear=True):
            module = _reload_module("tools.mcp_client")
            with self.assertRaisesRegex(ValueError, "McpServerGatewayUrl"):
                module.get_mcp_client()

    def test_resolve_service_defaults_to_bedrock_agentcore(self):
        with patch.dict(
            os.environ,
            {
                "McpServerGatewayUrl": "https://example.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
            },
            clear=True,
        ):
            module = _reload_module("tools.mcp_client")
            self.assertEqual(module._resolve_service(), "bedrock-agentcore")
            self.assertEqual(module._resolve_region(), "us-east-1")

    def test_get_mcp_client_starts_once_and_cleans_up(self):
        with patch.dict(
            os.environ,
            {
                "McpServerGatewayUrl": "https://example.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
            },
            clear=True,
        ):
            module = _reload_module("tools.mcp_client")
            fake_inner_client = MagicMock()

            with patch.object(module, "MCPClient", return_value=fake_inner_client):
                client_one = module.get_mcp_client()
                client_two = module.get_mcp_client()

            self.assertIs(client_one, client_two)
            self.assertEqual(
                client_one.server_url,
                "https://example.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
            )
            fake_inner_client.start.assert_called_once_with()

            module.cleanup_mcp_client()
            fake_inner_client.stop.assert_called_once_with(None, None, None)

    def test_auth_flow_removes_connection_header_and_uses_gateway_region(self):
        with patch.dict(
            os.environ,
            {
                "McpServerGatewayUrl": "https://example.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp",
            },
            clear=True,
        ):
            module = _reload_module("tools.mcp_client")

            request = SimpleNamespace(
                method="POST",
                url="https://example.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp",
                content=b"{}",
                headers={"connection": "keep-alive", "content-type": "application/json"},
            )

            fake_credentials = SimpleNamespace()
            captured = {}

            class CapturingAWSRequest:
                def __init__(self, method=None, url=None, data=None, headers=None):
                    captured["headers"] = headers or {}
                    self.method = method
                    self.url = url
                    self.data = data
                    self.headers = {"authorization": "signed"}

            class CapturingSigV4Auth:
                def __init__(self, credentials, service, region):
                    captured["credentials"] = credentials
                    captured["service"] = service
                    captured["region"] = region

                def add_auth(self, aws_request):
                    aws_request.headers["x-amz-date"] = "20260610T000000Z"

            with patch.object(module, "_resolve_frozen_credentials", return_value=fake_credentials):
                with patch.object(module, "AWSRequest", CapturingAWSRequest):
                    with patch.object(module, "BotocoreSigV4Auth", CapturingSigV4Auth):
                        flow = module.AwsSigV4Auth().auth_flow(request)
                        signed_request = next(flow)

            self.assertNotIn("connection", captured["headers"])
            self.assertEqual(captured["service"], "bedrock-agentcore")
            self.assertEqual(captured["region"], "us-west-2")
            self.assertEqual(signed_request.headers["authorization"], "signed")
            self.assertEqual(signed_request.headers["x-amz-date"], "20260610T000000Z")

    def test_transport_uses_sigv4_async_client_for_iam_gateway(self):
        with patch.dict(
            os.environ,
            {
                "McpServerGatewayUrl": "https://example.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
            },
            clear=True,
        ):
            module = _reload_module("tools.mcp_client")
            captured = {}

            class CapturingAsyncClient:
                def __init__(self, *args, **kwargs):
                    captured["async_client_kwargs"] = kwargs

                async def __aenter__(self):
                    captured["async_client_entered"] = True
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    captured["async_client_exited"] = True
                    return False

            def fake_streamable_http_client(url, http_client=None):
                captured["streamable_url"] = url
                captured["streamable_client"] = http_client

                class _TransportContext:
                    async def __aenter__(self_inner):
                        callback = lambda: "session-id"
                        captured["session_callback"] = callback
                        return ("read", "write", callback)

                    async def __aexit__(self_inner, exc_type, exc_val, exc_tb):
                        captured["streamable_exited"] = True
                        return False

                return _TransportContext()

            async def run_transport():
                gateway_client = module.StrandsGatewayMcpClient(
                    "https://example.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
                )
                with patch.object(module.httpx, "AsyncClient", CapturingAsyncClient):
                    with patch.object(module, "streamable_http_client", side_effect=fake_streamable_http_client):
                        async with gateway_client._create_transport() as streams:
                            self.assertEqual(streams[0], "read")
                            self.assertEqual(streams[1], "write")
                            self.assertIs(streams[2], captured["session_callback"])

            asyncio.run(run_transport())

            self.assertEqual(
                captured["streamable_url"],
                "https://example.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
            )
            self.assertIsInstance(
                captured["async_client_kwargs"]["auth"],
                module.AwsSigV4Auth,
            )
            self.assertTrue(captured.get("async_client_entered"))
            self.assertTrue(captured.get("async_client_exited"))
            self.assertTrue(captured.get("streamable_exited"))


class TestRobotActions(unittest.TestCase):
    def test_get_dynamic_tools_uses_pagination_and_filters(self):
        with patch.dict(
            os.environ,
            {
                "McpServerGatewayUrl": "https://example.gateway.aws",
                "MCP_TOOL_PREFIX_ALLOW": "robotics-mcp-lambda___robot_,robotics-mcp-lambda___drone_,robotics-mcp-lambda___xiaoice_",
                "MCP_TOOL_EXCLUDE": "robotics-mcp-lambda___robot_stop",
            },
            clear=True,
        ):
            mcp_client_module = _reload_module("tools.mcp_client")
            robot_actions = importlib.import_module("tools.robot_actions")

            fake_client = MagicMock()
            fake_client.list_tools_sync.side_effect = [
                PaginatedTools(
                    [FakeTool("robotics-mcp-lambda___robot_move")],
                    "next-page",
                ),
                PaginatedTools(
                    [FakeTool("robotics-mcp-lambda___drone_takeoff")],
                    None,
                ),
            ]

            with patch.object(mcp_client_module, "get_mcp_client", return_value=fake_client):
                with patch.object(robot_actions, "get_mcp_client", return_value=fake_client):
                    tools = robot_actions.get_dynamic_tools()

            self.assertEqual(
                [tool.tool_name for tool in tools],
                [
                    "robotics-mcp-lambda___robot_move",
                    "robotics-mcp-lambda___drone_takeoff",
                ],
            )
            self.assertEqual(fake_client.list_tools_sync.call_count, 2)
            self.assertEqual(tools[0].mcp_tool.name, "robotics-mcp-lambda___robot_move")
            self.assertEqual(tools[1].mcp_tool.name, "robotics-mcp-lambda___drone_takeoff")

            first_call = fake_client.list_tools_sync.call_args_list[0]
            second_call = fake_client.list_tools_sync.call_args_list[1]
            self.assertIsNone(first_call.kwargs["pagination_token"])
            self.assertEqual(second_call.kwargs["pagination_token"], "next-page")

            tool_filters = first_call.kwargs["tool_filters"]
            self.assertIn("allowed", tool_filters)
            self.assertIn("rejected", tool_filters)
            self.assertTrue(tool_filters["allowed"][0]({"name": "robotics-mcp-lambda___robot_walk"}))
            self.assertTrue(tool_filters["allowed"][0]({"name": "robotics-mcp-lambda___drone_land"}))
            self.assertTrue(tool_filters["allowed"][0]({"name": "robotics-mcp-lambda___xiaoice_speech"}))
            self.assertFalse(tool_filters["allowed"][0]({"name": "robotics-mcp-lambda___dog_stand_up"}))
            self.assertTrue(tool_filters["rejected"][0]({"name": "robotics-mcp-lambda___robot_stop"}))
            self.assertFalse(tool_filters["rejected"][0]({"name": "robotics-mcp-lambda___robot_walk"}))


if __name__ == "__main__":
    unittest.main()
