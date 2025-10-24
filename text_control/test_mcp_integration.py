#!/usr/bin/env python3
"""
Test script for MCP-based Strands agent integration
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_mcp_client():
    """Test MCP client creation"""
    print("=" * 60)
    print("Test 1: MCP Client Creation")
    print("=" * 60)

    try:
        import config
        from services.strands_service_mcp import create_mcp_client

        if not config.MCP_SERVER_URL:
            print("❌ MCP_SERVER_URL not configured")
            print(f"   Set McpServerUrl environment variable")
            return False

        print(f"✓ MCP_SERVER_URL: {config.MCP_SERVER_URL}")

        mcp_client = create_mcp_client()
        print("✓ MCP client created successfully")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_agent_with_mcp():
    """Test agent creation with MCP tools"""
    print("\n" + "=" * 60)
    print("Test 2: Agent Creation with MCP Tools")
    print("=" * 60)

    try:
        import config
        from services.strands_service_mcp import (
            create_mcp_client,
            create_robot_agent_with_mcp,
        )

        if not config.MCP_SERVER_URL:
            print("❌ MCP_SERVER_URL not configured")
            return False

        mcp_client = create_mcp_client()
        print("✓ MCP client created")

        with mcp_client:
            print("✓ MCP client context manager entered")

            # List available tools
            try:
                tools = mcp_client.list_tools_sync()
                print(f"✓ Found {len(tools)} MCP tools")

                # Show first few tools
                print("\nSample tools:")
                for i, tool in enumerate(tools[:5]):
                    print(f"  {i+1}. {tool.name}")
                if len(tools) > 5:
                    print(f"  ... and {len(tools) - 5} more")

            except Exception as e:
                print(f"⚠ Could not list tools: {e}")

            # Create agent
            agent = create_robot_agent_with_mcp("test_session", mcp_client)
            print("✓ Agent created with MCP tools")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_agent_command():
    """Test actual command execution"""
    print("\n" + "=" * 60)
    print("Test 3: Command Execution (Async)")
    print("=" * 60)

    try:
        import config
        from services.strands_service_mcp import (
            create_mcp_client,
            create_robot_agent_with_mcp,
        )

        if not config.MCP_SERVER_URL:
            print("❌ MCP_SERVER_URL not configured")
            return False

        mcp_client = create_mcp_client()

        async def run_command():
            with mcp_client:
                agent = create_robot_agent_with_mcp("test_session", mcp_client)
                print("✓ Agent ready")

                # Test a simple command
                command = "list available robots"
                print(f"\n→ Command: '{command}'")

                import time

                start_time = time.time()

                # Use streaming to see response as it comes
                print("← Response:")
                async for event in agent.stream_async(command):
                    event_data = event.get("data") or event.get("result", "")
                    if event_data:
                        print(f"   {event_data}", end="", flush=True)

                elapsed = time.time() - start_time
                print(f"\n\n✓ Command completed in {elapsed:.2f}s")

                return True

        return asyncio.run(run_command())

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_fallback_mode():
    """Test fallback to local tools when MCP unavailable"""
    print("\n" + "=" * 60)
    print("Test 4: Fallback Mode (Local Tools)")
    print("=" * 60)

    try:
        # Temporarily disable MCP
        import config

        original_url = config.MCP_SERVER_URL
        config.MCP_SERVER_URL = None

        from services.strands_service_mcp import create_robot_agent

        print("✓ MCP_SERVER_URL disabled for test")

        agent = create_robot_agent("test_fallback_session")
        print("✓ Agent created with local tools (fallback mode)")

        # Restore original URL
        config.MCP_SERVER_URL = original_url

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MCP Performance Optimization Tests" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")

    results = []

    # Test 1: MCP client creation
    results.append(("MCP Client Creation", test_mcp_client()))

    # Test 2: Agent with MCP tools
    if results[0][1]:  # Only if test 1 passed
        results.append(("Agent with MCP Tools", test_agent_with_mcp()))

        # Test 3: Command execution
        if results[1][1]:  # Only if test 2 passed
            results.append(("Command Execution", test_agent_command()))

    # Test 4: Fallback mode (always run)
    results.append(("Fallback Mode", test_fallback_mode()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
