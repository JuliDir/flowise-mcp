#!/usr/bin/env python3
"""
Flowise MCP Server

An MCP server that enables AI agents to interact with Flowise instances,
including managing chatflows, agentflows, making predictions, and analyzing
flow configurations for improvements.
"""

import json
from typing import Any

from fastmcp import FastMCP

from .client import get_config, handle_api_error, make_api_request
from .models import (
    AnalyzeFlowInput,
    CreateFlowInput,
    DeleteChatHistoryInput,
    DeleteFlowInput,
    GetAssistantInput,
    GetChatHistoryInput,
    GetDocumentStoreInput,
    GetFlowInput,
    ListAssistantsInput,
    ListDocumentStoresInput,
    ListFlowsInput,
    ListToolsInput,
    ListVariablesInput,
    PredictionInput,
    QueryVectorStoreInput,
    ResponseFormat,
    UpdateFlowInput,
    UpsertVectorInput,
)
from .utils import (
    analyze_flow_data,
    format_analysis,
    format_flow_detail,
    format_flow_list,
)

mcp = FastMCP(
    name="flowise_mcp",
    instructions="""
    Flowise MCP Server - Connect AI agents to Flowise instances.

    This server provides tools to:
    - List, create, update, and delete chatflows and agentflows
    - Make predictions (chat with flows)
    - Analyze flow configurations and suggest improvements
    - Manage variables, tools, and document stores
    - Retrieve chat history and feedback

    Use flowise_analyze_flow to get improvement suggestions for any flow.
    """,
)


# =============================================================================
# Tool Definitions
# =============================================================================


@mcp.tool(
    name="flowise_list_flows",
    annotations={
        "title": "List Flowise Flows",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_list_flows(params: ListFlowsInput) -> str:
    """
    List all chatflows and agentflows in the Flowise instance.

    This tool retrieves a summary of all available flows, including their
    deployment status, visibility, and categories.

    Args:
        params: Input parameters containing optional flow_type filter and response_format.

    Returns:
        A formatted list of all flows with their basic information.

    Examples:
        - List all flows: Use with no parameters
        - List only agentflows: Use flow_type='AGENTFLOW'
        - Get JSON output: Use response_format='json'
    """
    try:
        flows: list[dict[str, Any]] = await make_api_request("chatflows")

        if params.flow_type:
            flows = [f for f in flows if f.get("type") == params.flow_type.value]

        return format_flow_list(flows, params.response_format)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_get_flow",
    annotations={
        "title": "Get Flowise Flow Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_get_flow(params: GetFlowInput) -> str:
    """
    Get detailed information about a specific chatflow or agentflow.

    This tool retrieves the full configuration of a flow, including all
    nodes, edges, and settings.

    Args:
        params: Input containing flow_id and response_format.

    Returns:
        Detailed flow information including configuration and nodes.

    Examples:
        - Get flow details: Use with the flow ID from flowise_list_flows
    """
    try:
        flow = await make_api_request(f"chatflows/{params.flow_id}")
        return format_flow_detail(flow, params.response_format)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_predict",
    annotations={
        "title": "Send Message to Flowise Flow",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowise_predict(params: PredictionInput) -> str:
    """
    Send a message to a chatflow or agentflow and get a response.

    This is the primary tool for interacting with Flowise flows. It sends
    a question/message to the specified flow and returns the AI response.

    Args:
        params: Input containing flow_id, question, and optional session_id,
                streaming preference, and override_config.

    Returns:
        The response from the Flowise flow.

    Examples:
        - Simple question: Use flow_id and question
        - With session: Add session_id to maintain conversation context
        - Override settings: Use override_config to adjust temperature, etc.
    """
    try:
        payload: dict[str, Any] = {"question": params.question}

        if params.streaming:
            payload["streaming"] = True

        override_config: dict[str, Any] = {}
        if params.session_id:
            override_config["sessionId"] = params.session_id
        if params.override_config:
            override_config.update(params.override_config)
        if override_config:
            payload["overrideConfig"] = override_config

        response = await make_api_request(
            f"prediction/{params.flow_id}", method="POST", data=payload
        )

        if isinstance(response, dict):
            if "text" in response:
                return str(response["text"])
            elif "json" in response:
                return json.dumps(response["json"], indent=2)
            else:
                return json.dumps(response, indent=2)

        return str(response)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_analyze_flow",
    annotations={
        "title": "Analyze Flow and Suggest Improvements",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_analyze_flow(params: AnalyzeFlowInput) -> str:
    """
    Analyze a chatflow or agentflow and provide improvement suggestions.

    This tool examines the flow configuration and provides actionable
    recommendations for enhancing the flow's capabilities, performance,
    and best practices compliance.

    IMPORTANT: This is the primary tool for answering questions like
    "How can I improve this agentflow to do X?" or "What can I add to
    make my chatflow better at Y?"

    Args:
        params: Input containing flow_id, optional improvement_goal, and response_format.

    Returns:
        A detailed analysis with:
        - Current flow structure overview
        - Identified issues or gaps
        - Prioritized improvement suggestions
        - Best practices recommendations
        - Specific nodes to add or configure

    Examples:
        - General analysis: Use with just the flow_id
        - Targeted improvements: Add improvement_goal like "improve accuracy"
        - Speed optimization: Use improvement_goal="faster responses"
        - Add capabilities: Use improvement_goal="handle customer support queries"
    """
    try:
        flow = await make_api_request(f"chatflows/{params.flow_id}")
        analysis = analyze_flow_data(flow, params.improvement_goal)
        return format_analysis(analysis, params.response_format)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_create_flow",
    annotations={
        "title": "Create New Flowise Flow",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowise_create_flow(params: CreateFlowInput) -> str:
    """
    Create a new chatflow or agentflow in Flowise.

    This tool creates a new flow with the specified configuration.
    The flow_data should be a valid JSON string containing the nodes
    and edges configuration.

    Args:
        params: Input containing name, flow_data (JSON), flow_type, is_public, and category.

    Returns:
        The created flow's details including its new ID.

    Examples:
        - Create a simple chatflow with a name and empty flow_data: '{}'
        - Create an agentflow: Set flow_type='AGENTFLOW'
    """
    try:
        payload: dict[str, Any] = {
            "name": params.name,
            "flowData": params.flow_data,
            "type": params.flow_type.value,
        }

        if params.is_public:
            payload["isPublic"] = True
        if params.category:
            payload["category"] = params.category

        response = await make_api_request("chatflows", method="POST", data=payload)

        return f"Flow created successfully!\n\n**ID**: `{response.get('id')}`\n**Name**: {response.get('name')}"
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_update_flow",
    annotations={
        "title": "Update Flowise Flow",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_update_flow(params: UpdateFlowInput) -> str:
    """
    Update an existing chatflow or agentflow.

    This tool updates the specified flow with new configuration.
    Only provided fields will be updated.

    Args:
        params: Input containing flow_id and optional fields to update.

    Returns:
        Confirmation of the update with the flow's details.

    Examples:
        - Rename a flow: Use flow_id and name
        - Update configuration: Use flow_id and flow_data
        - Make public: Use flow_id and is_public=True
    """
    try:
        payload: dict[str, Any] = {}

        if params.name is not None:
            payload["name"] = params.name
        if params.flow_data is not None:
            payload["flowData"] = params.flow_data
        if params.is_public is not None:
            payload["isPublic"] = params.is_public
        if params.category is not None:
            payload["category"] = params.category

        if not payload:
            return "Error: No fields provided to update."

        response = await make_api_request(f"chatflows/{params.flow_id}", method="PUT", data=payload)

        return f"Flow updated successfully!\n\n**ID**: `{response.get('id')}`\n**Name**: {response.get('name')}"
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_delete_flow",
    annotations={
        "title": "Delete Flowise Flow",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_delete_flow(params: DeleteFlowInput) -> str:
    """
    Delete a chatflow or agentflow from Flowise.

    WARNING: This action is irreversible. The flow and its configuration
    will be permanently deleted.

    Args:
        params: Input containing the flow_id to delete.

    Returns:
        Confirmation of deletion.
    """
    try:
        await make_api_request(f"chatflows/{params.flow_id}", method="DELETE")
        return f"Flow `{params.flow_id}` has been deleted successfully."
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_get_chat_history",
    annotations={
        "title": "Get Chat History",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_get_chat_history(params: GetChatHistoryInput) -> str:
    """
    Retrieve chat message history for a specific flow.

    This tool gets the conversation history from a chatflow or agentflow,
    useful for reviewing past interactions or debugging.

    Args:
        params: Input containing flow_id, optional session_id, limit, and response_format.

    Returns:
        List of chat messages with timestamps and content.
    """
    try:
        query_params = {"chatflowid": params.flow_id}
        if params.session_id:
            query_params["sessionId"] = params.session_id

        messages = await make_api_request("chatmessage", params=query_params)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                messages[: params.limit] if isinstance(messages, list) else messages, indent=2
            )

        if not messages:
            return "No chat history found for this flow."

        lines = ["# Chat History\n"]
        msg_list: list[dict[str, Any]] = (
            messages[: params.limit] if isinstance(messages, list) else []
        )

        for msg in msg_list:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("createdDate", "N/A")
            role_indicator = "[USER]" if role == "user" else "[BOT]"

            lines.append(f"### {role_indicator} {role.title()} ({timestamp})")
            lines.append(f"{content[:500]}{'...' if len(content) > 500 else ''}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_list_variables",
    annotations={
        "title": "List Flowise Variables",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_list_variables(params: ListVariablesInput) -> str:
    """
    List all global variables configured in Flowise.

    Variables can be used across flows for storing API keys, URLs,
    or other configuration values.

    Args:
        params: Input containing response_format.

    Returns:
        List of configured variables.
    """
    try:
        variables: list[dict[str, Any]] = await make_api_request("variables")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(variables, indent=2)

        if not variables:
            return "No variables configured."

        lines = ["# Flowise Variables\n"]
        for var in variables:
            full_value = str(var.get("value", ""))
            display_value = full_value[:50] + "..." if len(full_value) > 50 else full_value
            lines.append(f"- **{var.get('name', 'Unnamed')}**: `{display_value}`")

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_list_tools",
    annotations={
        "title": "List Available Tools",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_list_tools(params: ListToolsInput) -> str:
    """
    List all tools available in Flowise.

    This retrieves the list of registered tools that can be used
    in agentflows and chatflows.

    Args:
        params: Input containing response_format.

    Returns:
        List of available tools with their descriptions.
    """
    try:
        tools: list[dict[str, Any]] = await make_api_request("tools")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(tools, indent=2)

        if not tools:
            return "No custom tools configured."

        lines = ["# Available Tools\n"]
        for tool in tools:
            lines.append(f"## {tool.get('name', 'Unnamed')}")
            if tool.get("description"):
                lines.append(str(tool.get("description")))
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_ping",
    annotations={
        "title": "Ping Flowise Server",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_ping() -> str:
    """
    Check if the Flowise server is reachable and responding.

    Use this tool to verify connectivity before making other requests.

    Returns:
        Server status message.
    """
    try:
        await make_api_request("ping")
        config = get_config()
        return f"Flowise server at `{config['base_url']}` is responding."
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_list_assistants",
    annotations={
        "title": "List Flowise Assistants",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_list_assistants(params: ListAssistantsInput) -> str:
    """
    List all assistants configured in Flowise.

    Assistants are pre-configured AI agents that can be used for specific tasks.

    Args:
        params: Input containing response_format.

    Returns:
        List of configured assistants.
    """
    try:
        assistants: list[dict[str, Any]] = await make_api_request("assistants")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(assistants, indent=2)

        if not assistants:
            return "No assistants configured."

        lines = ["# Flowise Assistants\n"]
        for assistant in assistants:
            lines.append(f"## {assistant.get('name', 'Unnamed')}")
            lines.append(f"- **ID**: `{assistant.get('id', 'N/A')}`")
            lines.append(f"- **Model**: {assistant.get('model', 'N/A')}")
            if assistant.get("description"):
                lines.append(f"- **Description**: {assistant.get('description')}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_get_assistant",
    annotations={
        "title": "Get Assistant Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_get_assistant(params: GetAssistantInput) -> str:
    """
    Get detailed information about a specific assistant.

    Args:
        params: Input containing assistant_id and response_format.

    Returns:
        Detailed assistant information including configuration.
    """
    try:
        assistant = await make_api_request(f"assistants/{params.assistant_id}")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(assistant, indent=2)

        lines = [
            f"# Assistant: {assistant.get('name', 'Unnamed')}",
            "",
            f"**ID**: `{assistant.get('id', 'N/A')}`",
            f"**Model**: {assistant.get('model', 'N/A')}",
            f"**Temperature**: {assistant.get('temperature', 'N/A')}",
            f"**Top P**: {assistant.get('top_p', 'N/A')}",
        ]

        if assistant.get("description"):
            lines.append(f"**Description**: {assistant.get('description')}")

        if assistant.get("instructions"):
            lines.append("")
            lines.append("## Instructions")
            lines.append(str(assistant.get("instructions"))[:500])

        if assistant.get("tools"):
            lines.append("")
            lines.append("## Tools")
            for tool in assistant.get("tools", []):
                lines.append(f"- {tool.get('type', 'Unknown')}")

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_delete_chat_history",
    annotations={
        "title": "Delete Chat History",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_delete_chat_history(params: DeleteChatHistoryInput) -> str:
    """
    Delete chat message history for a specific flow.

    This removes conversation history from the database. Use with caution.

    Args:
        params: Input containing flow_id, optional session_id and chat_id.

    Returns:
        Confirmation of deletion.
    """
    try:
        query_params: dict[str, str] = {}
        if params.session_id:
            query_params["sessionId"] = params.session_id
        if params.chat_id:
            query_params["chatId"] = params.chat_id

        await make_api_request(
            f"chatmessage/{params.flow_id}",
            method="DELETE",
            params=query_params if query_params else None,
        )

        scope = "all messages"
        if params.session_id:
            scope = f"session `{params.session_id}`"
        elif params.chat_id:
            scope = f"chat `{params.chat_id}`"

        return f"Chat history deleted for flow `{params.flow_id}` ({scope})."
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_list_document_stores",
    annotations={
        "title": "List Document Stores",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_list_document_stores(params: ListDocumentStoresInput) -> str:
    """
    List all document stores configured in Flowise.

    Document stores contain indexed documents for RAG (Retrieval-Augmented Generation).

    Args:
        params: Input containing response_format.

    Returns:
        List of document stores with their details.
    """
    try:
        stores: list[dict[str, Any]] = await make_api_request("document-store/store")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(stores, indent=2)

        if not stores:
            return "No document stores configured."

        lines = ["# Document Stores\n"]
        for store in stores:
            lines.append(f"## {store.get('name', 'Unnamed')}")
            lines.append(f"- **ID**: `{store.get('id', 'N/A')}`")
            lines.append(f"- **Status**: {store.get('status', 'N/A')}")
            if store.get("description"):
                lines.append(f"- **Description**: {store.get('description')}")
            lines.append(f"- **Updated**: {store.get('updatedDate', 'N/A')}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_get_document_store",
    annotations={
        "title": "Get Document Store Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_get_document_store(params: GetDocumentStoreInput) -> str:
    """
    Get detailed information about a specific document store.

    Args:
        params: Input containing store_id and response_format.

    Returns:
        Detailed document store information.
    """
    try:
        store = await make_api_request(f"document-store/store/{params.store_id}")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(store, indent=2)

        lines = [
            f"# Document Store: {store.get('name', 'Unnamed')}",
            "",
            f"**ID**: `{store.get('id', 'N/A')}`",
            f"**Status**: {store.get('status', 'N/A')}",
            f"**Created**: {store.get('createdDate', 'N/A')}",
            f"**Updated**: {store.get('updatedDate', 'N/A')}",
        ]

        if store.get("description"):
            lines.append(f"**Description**: {store.get('description')}")

        if store.get("loaders"):
            lines.append("")
            lines.append("## Document Loaders")
            for loader in store.get("loaders", []):
                lines.append(f"- **{loader.get('loaderName', 'Unknown')}**: {loader.get('status', 'N/A')}")

        return "\n".join(lines)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_upsert_vector",
    annotations={
        "title": "Upsert Vectors to Flow",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def flowise_upsert_vector(params: UpsertVectorInput) -> str:
    """
    Insert or update vectors in a chatflow's vector store.

    This triggers the flow's document processing pipeline to update the vector store.

    Args:
        params: Input containing flow_id, optional override_config and stop_node_id.

    Returns:
        Summary of the upsert operation results.
    """
    try:
        payload: dict[str, Any] = {}

        if params.stop_node_id:
            payload["stopNodeId"] = params.stop_node_id
        if params.override_config:
            payload["overrideConfig"] = params.override_config

        response = await make_api_request(
            f"vector/upsert/{params.flow_id}",
            method="POST",
            data=payload if payload else None,
        )

        if isinstance(response, dict):
            added = response.get("numAdded", 0)
            updated = response.get("numUpdated", 0)
            deleted = response.get("numDeleted", 0)
            skipped = response.get("numSkipped", 0)

            return (
                f"Vector upsert completed for flow `{params.flow_id}`:\n\n"
                f"- **Added**: {added}\n"
                f"- **Updated**: {updated}\n"
                f"- **Deleted**: {deleted}\n"
                f"- **Skipped**: {skipped}"
            )

        return f"Vector upsert completed: {response}"
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="flowise_query_vector_store",
    annotations={
        "title": "Query Vector Store",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def flowise_query_vector_store(params: QueryVectorStoreInput) -> str:
    """
    Execute a retrieval query on a document store's vector store.

    This searches for relevant documents based on the query.

    Args:
        params: Input containing store_id and query.

    Returns:
        Retrieved documents with relevance information.
    """
    try:
        response = await make_api_request(
            "document-store/vectorstore/query",
            method="POST",
            data={"storeId": params.store_id, "query": params.query},
        )

        if isinstance(response, dict):
            time_taken = response.get("timeTaken", "N/A")
            docs = response.get("docs", [])

            lines = [
                f"# Query Results",
                "",
                f"**Query**: {params.query}",
                f"**Time**: {time_taken}ms",
                f"**Results**: {len(docs)} documents",
                "",
            ]

            for i, doc in enumerate(docs[:10], 1):
                content = doc.get("pageContent", "")[:300]
                lines.append(f"## Document {i}")
                lines.append(f"{content}{'...' if len(doc.get('pageContent', '')) > 300 else ''}")
                if doc.get("metadata"):
                    source = doc["metadata"].get("source", "Unknown")
                    lines.append(f"*Source: {source}*")
                lines.append("")

            return "\n".join(lines)

        return json.dumps(response, indent=2)
    except Exception as e:
        return handle_api_error(e)


# =============================================================================
# Prompts
# =============================================================================


@mcp.prompt(name="analyze_agentflow")
def analyze_agentflow_prompt(flow_id: str, goal: str = "") -> str:
    """
    Prompt template for analyzing an agentflow and suggesting improvements.
    """
    goal_text = f"\n\nSpecific goal: {goal}" if goal else ""
    return f"""Please analyze the Flowise agentflow with ID: {flow_id}{goal_text}

Steps to follow:
1. First, use flowise_get_flow to retrieve the full flow configuration
2. Then, use flowise_analyze_flow with the flow_id to get improvement suggestions
3. Based on the analysis, provide specific, actionable recommendations

Consider:
- Current nodes and their connections
- Missing components (memory, tools, retrieval)
- Performance optimization opportunities
- Best practices for the flow type
- The specific goal if provided"""


@mcp.prompt(name="improve_chatbot")
def improve_chatbot_prompt(flow_id: str, issue: str) -> str:
    """
    Prompt template for improving a chatbot based on a specific issue.
    """
    return f"""Help me improve my Flowise chatbot (flow ID: {flow_id}).

Issue I'm experiencing: {issue}

Please:
1. Use flowise_get_flow to examine the current configuration
2. Use flowise_analyze_flow with improvement_goal set to address my issue
3. Provide step-by-step recommendations
4. Suggest specific nodes to add or configure"""


# =============================================================================
# Resources
# =============================================================================


@mcp.resource("flowise://flows")
async def list_all_flows() -> str:
    """Resource to get all flows as a JSON list."""
    try:
        flows = await make_api_request("chatflows")
        return json.dumps(flows, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("flowise://flow/{flow_id}")
async def get_flow_resource(flow_id: str) -> str:
    """Resource to get a specific flow's configuration."""
    try:
        flow = await make_api_request(f"chatflows/{flow_id}")
        return json.dumps(flow, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    mcp.run()
