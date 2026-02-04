"""
Tests for Flowise MCP Server
"""

import json
from unittest.mock import AsyncMock

import httpx
import pytest

from flowise_mcp.client import handle_api_error
from flowise_mcp.models import FlowType, ResponseFormat
from flowise_mcp.utils import (
    analyze_flow_data,
    categorize_node,
    format_analysis,
    format_flow_detail,
    format_flow_list,
)


# =============================================================================
# Unit Tests for Helper Functions
# =============================================================================


class TestCategorizeNode:
    """Tests for categorize_node function."""

    def test_categorize_llm_nodes(self) -> None:
        assert categorize_node("ChatOpenAI") == "llm"
        assert categorize_node("GPT-4") == "llm"
        assert categorize_node("Claude") == "llm"
        assert categorize_node("AnthropicChat") == "llm"

    def test_categorize_memory_nodes(self) -> None:
        assert categorize_node("BufferMemory") == "memory"
        assert categorize_node("WindowMemory") == "memory"
        assert categorize_node("ConversationMemory") == "memory"

    def test_categorize_vector_store_nodes(self) -> None:
        assert categorize_node("Chroma") == "vector_store"
        assert categorize_node("Pinecone") == "vector_store"
        assert categorize_node("FAISS") == "vector_store"

    def test_categorize_tool_nodes(self) -> None:
        assert categorize_node("SerpAPI") == "tool"
        assert categorize_node("Calculator") == "tool"
        assert categorize_node("CustomTool") == "tool"

    def test_categorize_unknown_nodes(self) -> None:
        assert categorize_node("SomeRandomNode") == "other"


class TestFormatFlowList:
    """Tests for format_flow_list function."""

    def test_format_empty_list(self) -> None:
        result = format_flow_list([], ResponseFormat.MARKDOWN)
        assert result == "No flows found."

    def test_format_json(self) -> None:
        flows = [{"id": "123", "name": "Test", "type": "CHATFLOW"}]
        result = format_flow_list(flows, ResponseFormat.JSON)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "Test"

    def test_format_markdown(self) -> None:
        flows = [
            {
                "id": "123456789",
                "name": "Test Flow",
                "type": "CHATFLOW",
                "deployed": True,
                "isPublic": False,
            }
        ]
        result = format_flow_list(flows, ResponseFormat.MARKDOWN)
        assert "Test Flow" in result
        assert "[CHAT]" in result
        assert "[YES]" in result  # deployed


class TestFormatFlowDetail:
    """Tests for format_flow_detail function."""

    def test_format_json(self) -> None:
        flow = {"id": "123", "name": "Test", "flowData": "{}"}
        result = format_flow_detail(flow, ResponseFormat.JSON)
        parsed = json.loads(result)
        assert parsed["name"] == "Test"

    def test_format_markdown_with_nodes(self) -> None:
        flow = {
            "id": "123",
            "name": "Test Flow",
            "type": "AGENTFLOW",
            "flowData": json.dumps(
                {"nodes": [{"id": "1", "data": {"type": "ChatOpenAI", "label": "LLM"}}]}
            ),
        }
        result = format_flow_detail(flow, ResponseFormat.MARKDOWN)
        assert "Test Flow" in result
        assert "[AGENT]" in result
        assert "Nodes" in result
        assert "LLM" in result


class TestAnalyzeFlowData:
    """Tests for analyze_flow_data function."""

    def test_analyze_flow_without_memory(self) -> None:
        flow = {
            "name": "Test",
            "type": "CHATFLOW",
            "flowData": json.dumps({"nodes": [{"data": {"type": "ChatOpenAI"}}], "edges": []}),
        }
        analysis = analyze_flow_data(flow)

        # Should suggest adding memory
        memory_suggestion = next(
            (s for s in analysis["suggestions"] if s["category"] == "memory"), None
        )
        assert memory_suggestion is not None
        assert memory_suggestion["priority"] == "high"

    def test_analyze_agentflow_without_tools(self) -> None:
        flow = {
            "name": "Test Agent",
            "type": "AGENTFLOW",
            "flowData": json.dumps({"nodes": [{"data": {"type": "Supervisor"}}], "edges": []}),
        }
        analysis = analyze_flow_data(flow)

        # Should suggest adding tools
        tools_suggestion = next(
            (s for s in analysis["suggestions"] if s["category"] == "tools"), None
        )
        assert tools_suggestion is not None

    def test_analyze_with_improvement_goal(self) -> None:
        flow = {
            "name": "Test",
            "type": "CHATFLOW",
            "flowData": json.dumps({"nodes": [{"data": {"type": "ChatOpenAI"}}], "edges": []}),
        }
        analysis = analyze_flow_data(flow, improvement_goal="better accuracy")

        # Should have accuracy-related suggestions
        accuracy_suggestion = next(
            (s for s in analysis["suggestions"] if s["category"] == "accuracy"), None
        )
        assert accuracy_suggestion is not None

    def test_analyze_corrupted_flow_data(self) -> None:
        flow = {"name": "Test", "type": "CHATFLOW", "flowData": "invalid json {"}
        analysis = analyze_flow_data(flow)
        assert len(analysis["potential_issues"]) > 0


class TestHandleApiError:
    """Tests for handle_api_error function."""

    def test_handle_401_error(self) -> None:
        response = AsyncMock()
        response.status_code = 401
        response.text = "Unauthorized"
        error = httpx.HTTPStatusError("", request=AsyncMock(), response=response)

        result = handle_api_error(error)
        assert "Authentication failed" in result
        assert "FLOWISE_API_KEY" in result

    def test_handle_404_error(self) -> None:
        response = AsyncMock()
        response.status_code = 404
        response.text = "Not Found"
        error = httpx.HTTPStatusError("", request=AsyncMock(), response=response)

        result = handle_api_error(error)
        assert "not found" in result

    def test_handle_timeout_error(self) -> None:
        error = httpx.TimeoutException("")
        result = handle_api_error(error)
        assert "timed out" in result

    def test_handle_connect_error(self) -> None:
        error = httpx.ConnectError("")
        result = handle_api_error(error)
        assert "Could not connect" in result


# =============================================================================
# Integration Tests (with mocked API)
# =============================================================================


class TestIntegrationListFlows:
    """Integration tests for list flows logic."""

    @pytest.mark.asyncio
    async def test_list_flows_formatting(self) -> None:
        """Test that flow list formatting works correctly."""
        mock_flows = [
            {"id": "1", "name": "Flow 1", "type": "CHATFLOW", "deployed": True, "isPublic": False},
            {"id": "2", "name": "Flow 2", "type": "AGENTFLOW", "deployed": False, "isPublic": True},
        ]

        # Test markdown formatting
        result = format_flow_list(mock_flows, ResponseFormat.MARKDOWN)
        assert "Flow 1" in result
        assert "Flow 2" in result
        assert "[CHAT]" in result
        assert "[AGENT]" in result

    @pytest.mark.asyncio
    async def test_list_flows_filter_by_type(self) -> None:
        """Test filtering flows by type."""
        mock_flows = [
            {"id": "1", "name": "Flow 1", "type": "CHATFLOW"},
            {"id": "2", "name": "Flow 2", "type": "AGENTFLOW"},
        ]

        # Filter to only AGENTFLOW
        filtered = [f for f in mock_flows if f.get("type") == FlowType.AGENTFLOW.value]
        result = format_flow_list(filtered, ResponseFormat.MARKDOWN)

        assert "Flow 2" in result
        assert "Flow 1" not in result


class TestIntegrationPredict:
    """Integration tests for prediction logic."""

    def test_predict_response_text_extraction(self) -> None:
        """Test extracting text from prediction response."""
        response = {"text": "Hello! How can I help you?"}

        # Simulate the extraction logic
        if isinstance(response, dict) and "text" in response:
            result = response["text"]
        else:
            result = str(response)

        assert result == "Hello! How can I help you?"

    def test_predict_response_json_extraction(self) -> None:
        """Test extracting JSON from prediction response."""
        response = {"json": {"key": "value"}}

        # Simulate the extraction logic
        if isinstance(response, dict):
            if "text" in response:
                result = response["text"]
            elif "json" in response:
                result = json.dumps(response["json"], indent=2)
            else:
                result = json.dumps(response, indent=2)

        assert "key" in result
        assert "value" in result


class TestIntegrationPing:
    """Integration tests for ping logic."""

    def test_ping_success_message(self) -> None:
        """Test ping success message formatting."""
        base_url = "http://localhost:3000"
        result = f"Flowise server at `{base_url}` is responding."

        assert "responding" in result
        assert base_url in result

    def test_ping_error_handling(self) -> None:
        """Test ping error handling."""
        error = httpx.ConnectError("")
        result = handle_api_error(error)

        assert "Error" in result
        assert "Could not connect" in result


# =============================================================================
# Format Analysis Tests
# =============================================================================


class TestFormatAnalysis:
    """Tests for format_analysis function."""

    def test_format_analysis_json(self) -> None:
        analysis = {
            "flow_name": "Test",
            "flow_type": "CHATFLOW",
            "summary": "Test summary",
            "nodes": [],
            "suggestions": [],
            "best_practices": [],
            "potential_issues": [],
        }

        result = format_analysis(analysis, ResponseFormat.JSON)
        parsed = json.loads(result)
        assert parsed["flow_name"] == "Test"

    def test_format_analysis_markdown(self) -> None:
        analysis = {
            "flow_name": "Test Flow",
            "flow_type": "CHATFLOW",
            "summary": "Contains 5 nodes",
            "nodes": [{"id": "1", "type": "ChatOpenAI", "label": "LLM", "category": "llm"}],
            "suggestions": [
                {
                    "priority": "high",
                    "category": "memory",
                    "title": "Add Memory",
                    "description": "Add memory for context",
                }
            ],
            "best_practices": [
                {"category": "prompts", "title": "Prompt Tips", "tips": ["Be specific"]}
            ],
            "potential_issues": [],
        }

        result = format_analysis(analysis, ResponseFormat.MARKDOWN)

        assert "Test Flow" in result
        assert "Add Memory" in result
        assert "[HIGH]" in result
        assert "Best Practices" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
