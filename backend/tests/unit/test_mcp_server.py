"""
Unit tests for MCP server: tools list, initialize, unknown method.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mcp_server import DocumentTranslatorMCPServer


@pytest.fixture
def mcp_server():
    return DocumentTranslatorMCPServer()


class TestGetTools:
    def test_returns_three_tools(self, mcp_server):
        tools = mcp_server.get_tools()
        assert len(tools) == 3
        names = {t["name"] for t in tools}
        assert "translate_text" in names
        assert "translate_file" in names
        assert "extract_text_from_file" in names

    def test_each_tool_has_name_description_input_schema(self, mcp_server):
        tools = mcp_server.get_tools()
        for t in tools:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t
            assert t["inputSchema"].get("type") == "object"


class TestHandleMcpRequest:
    @pytest.mark.asyncio
    async def test_initialize_returns_capabilities(self, mcp_server):
        result = await mcp_server.handle_mcp_request({
            "method": "initialize",
            "params": {}
        })
        assert "error" not in result
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "document-translator"

    @pytest.mark.asyncio
    async def test_tools_list_returns_tools_array(self, mcp_server):
        result = await mcp_server.handle_mcp_request({
            "method": "tools/list",
            "params": {}
        })
        assert "error" not in result
        assert "tools" in result
        assert len(result["tools"]) == 3

    @pytest.mark.asyncio
    async def test_unknown_method_returns_error(self, mcp_server):
        result = await mcp_server.handle_mcp_request({
            "method": "unknown/method",
            "params": {}
        })
        assert "error" in result
        assert result["error"]["code"] == -32601
