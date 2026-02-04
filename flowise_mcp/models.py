"""
Pydantic models and enums for Flowise MCP Server.
"""

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# Enums
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class FlowType(str, Enum):
    """Type of Flowise flow."""

    CHATFLOW = "CHATFLOW"
    AGENTFLOW = "AGENTFLOW"


# =============================================================================
# Input Models
# =============================================================================


class ListFlowsInput(BaseModel):
    """Input model for listing flows."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_type: FlowType | None = Field(
        default=None,
        description="Filter by flow type: 'CHATFLOW' or 'AGENTFLOW'. Leave empty for all.",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class GetFlowInput(BaseModel):
    """Input model for getting a specific flow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(
        ..., description="The unique identifier of the chatflow or agentflow", min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class PredictionInput(BaseModel):
    """Input model for making predictions (chatting with a flow)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(
        ..., description="The chatflow or agentflow ID to send the message to", min_length=1
    )
    question: str = Field(..., description="The message/question to send to the flow", min_length=1)
    session_id: str | None = Field(
        default=None, description="Optional session ID for maintaining conversation context"
    )
    streaming: bool = Field(
        default=False, description="Whether to use streaming responses (not recommended for MCP)"
    )
    override_config: dict[str, Any] | None = Field(
        default=None, description="Optional configuration overrides (e.g., temperature, maxTokens)"
    )


class AnalyzeFlowInput(BaseModel):
    """Input model for analyzing a flow and getting improvement suggestions."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(..., description="The chatflow or agentflow ID to analyze", min_length=1)
    improvement_goal: str | None = Field(
        default=None,
        description="Specific goal for improvement (e.g., 'better accuracy', 'faster responses', 'handle X type of queries')",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class CreateFlowInput(BaseModel):
    """Input model for creating a new flow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ..., description="Name of the new chatflow or agentflow", min_length=1, max_length=200
    )
    flow_data: str = Field(
        ..., description="JSON string containing the flow configuration (nodes and edges)"
    )
    flow_type: FlowType = Field(
        default=FlowType.CHATFLOW, description="Type of flow: 'CHATFLOW' or 'AGENTFLOW'"
    )
    is_public: bool = Field(
        default=False, description="Whether the flow should be publicly accessible"
    )
    category: str | None = Field(
        default=None,
        description="Categories for the flow, separated by semicolons (e.g., 'category1;category2')",
    )

    @field_validator("flow_data")
    @classmethod
    def validate_flow_data(cls, v: str) -> str:
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError("flow_data must be a valid JSON string") from e
        return v


class UpdateFlowInput(BaseModel):
    """Input model for updating an existing flow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(
        ..., description="The unique identifier of the flow to update", min_length=1
    )
    name: str | None = Field(default=None, description="New name for the flow")
    flow_data: str | None = Field(default=None, description="New flow configuration as JSON string")
    is_public: bool | None = Field(
        default=None, description="Whether the flow should be publicly accessible"
    )
    category: str | None = Field(default=None, description="New categories for the flow")

    @field_validator("flow_data")
    @classmethod
    def validate_flow_data(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError("flow_data must be a valid JSON string") from e
        return v


class DeleteFlowInput(BaseModel):
    """Input model for deleting a flow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(
        ..., description="The unique identifier of the flow to delete", min_length=1
    )


class GetChatHistoryInput(BaseModel):
    """Input model for getting chat history."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(..., description="The chatflow or agentflow ID", min_length=1)
    session_id: str | None = Field(
        default=None, description="Optional session ID to filter messages"
    )
    limit: int = Field(
        default=50, description="Maximum number of messages to retrieve", ge=1, le=500
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListVariablesInput(BaseModel):
    """Input model for listing variables."""

    model_config = ConfigDict(str_strip_whitespace=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListToolsInput(BaseModel):
    """Input model for listing available tools."""

    model_config = ConfigDict(str_strip_whitespace=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListAssistantsInput(BaseModel):
    """Input model for listing assistants."""

    model_config = ConfigDict(str_strip_whitespace=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetAssistantInput(BaseModel):
    """Input model for getting a specific assistant."""

    model_config = ConfigDict(str_strip_whitespace=True)

    assistant_id: str = Field(..., description="The unique identifier of the assistant", min_length=1)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class DeleteChatHistoryInput(BaseModel):
    """Input model for deleting chat history."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(..., description="The chatflow or agentflow ID", min_length=1)
    session_id: str | None = Field(default=None, description="Optional session ID to delete specific session")
    chat_id: str | None = Field(default=None, description="Optional chat ID to delete specific chat")


class ListDocumentStoresInput(BaseModel):
    """Input model for listing document stores."""

    model_config = ConfigDict(str_strip_whitespace=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetDocumentStoreInput(BaseModel):
    """Input model for getting a specific document store."""

    model_config = ConfigDict(str_strip_whitespace=True)

    store_id: str = Field(..., description="The unique identifier of the document store", min_length=1)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class UpsertVectorInput(BaseModel):
    """Input model for upserting vectors to a chatflow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    flow_id: str = Field(..., description="The chatflow ID containing the vector store", min_length=1)
    override_config: dict[str, Any] | None = Field(
        default=None, description="Optional configuration overrides for the upsert operation"
    )
    stop_node_id: str | None = Field(
        default=None, description="Node ID when multiple vector stores exist in the flow"
    )


class QueryVectorStoreInput(BaseModel):
    """Input model for querying a vector store."""

    model_config = ConfigDict(str_strip_whitespace=True)

    store_id: str = Field(..., description="The document store ID to query", min_length=1)
    query: str = Field(..., description="The search query", min_length=1)
