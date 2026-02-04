"""
Flowise MCP Server

An MCP server that enables AI agents to interact with Flowise instances,
including managing chatflows, agentflows, making predictions, and analyzing
flow configurations for improvements.
"""

from .client import (
    AuthenticationError,
    ConnectionError,
    FlowiseClientError,
    get_config,
    handle_api_error,
    make_api_request,
)
from .models import (
    AnalyzeFlowInput,
    CreateFlowInput,
    DeleteFlowInput,
    FlowType,
    GetChatHistoryInput,
    GetFlowInput,
    ListFlowsInput,
    ListToolsInput,
    ListVariablesInput,
    PredictionInput,
    ResponseFormat,
    UpdateFlowInput,
)
from .server import mcp
from .utils import (
    analyze_flow_data,
    categorize_node,
    format_analysis,
    format_flow_detail,
    format_flow_list,
)

__version__ = "0.1.0"
__all__ = [
    # Server
    "mcp",
    # Client
    "get_config",
    "handle_api_error",
    "make_api_request",
    # Exceptions
    "FlowiseClientError",
    "AuthenticationError",
    "ConnectionError",
    # Enums
    "FlowType",
    "ResponseFormat",
    # Models
    "AnalyzeFlowInput",
    "CreateFlowInput",
    "DeleteFlowInput",
    "GetChatHistoryInput",
    "GetFlowInput",
    "ListFlowsInput",
    "ListToolsInput",
    "ListVariablesInput",
    "PredictionInput",
    "UpdateFlowInput",
    # Utils
    "analyze_flow_data",
    "categorize_node",
    "format_analysis",
    "format_flow_detail",
    "format_flow_list",
]
