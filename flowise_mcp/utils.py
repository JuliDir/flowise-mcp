"""
Utility functions for formatting and analyzing Flowise flows.
"""

import json

from .models import ResponseFormat

# =============================================================================
# Formatters
# =============================================================================


def format_flow_list(flows: list[dict], format_type: ResponseFormat) -> str:
    """Format a list of flows for output."""
    simplified_flows = [
        {
            "id": flow.get("id"),
            "name": flow.get("name"),
            "type": flow.get("type", "CHATFLOW"),
            "deployed": flow.get("deployed", False),
            "isPublic": flow.get("isPublic", False),
            "category": flow.get("category"),
            "updatedDate": flow.get("updatedDate"),
        }
        for flow in flows
    ]

    if format_type == ResponseFormat.JSON:
        return json.dumps(simplified_flows, indent=2)

    if not flows:
        return "No flows found."

    lines = ["# Flowise Flows\n"]
    for flow in simplified_flows:
        flow_type = flow.get("type", "CHATFLOW")
        type_indicator = "[AGENT]" if flow_type in ("AGENTFLOW", "MULTIAGENT") else "[CHAT]"
        deployed = "[YES]" if flow.get("deployed") else "[NO]"
        public = "[PUBLIC]" if flow.get("isPublic") else "[PRIVATE]"

        lines.append(f"## {type_indicator} {flow.get('name', 'Unnamed')}")
        lines.append(f"- **ID**: `{flow.get('id', 'N/A')}`")
        lines.append(f"- **Type**: {flow_type}")
        lines.append(f"- **Deployed**: {deployed}")
        lines.append(f"- **Public**: {public}")
        if flow.get("category"):
            lines.append(f"- **Categories**: {flow.get('category')}")
        lines.append(f"- **Updated**: {flow.get('updatedDate', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def format_flow_detail(flow: dict, format_type: ResponseFormat) -> str:
    """Format detailed flow information for output."""
    flow_type = flow.get("type", "CHATFLOW")
    type_indicator = "[AGENT]" if flow_type in ("AGENTFLOW", "MULTIAGENT") else "[CHAT]"

    nodes_summary = []
    flow_data_str = flow.get("flowData", "{}")
    try:
        flow_data = json.loads(flow_data_str) if isinstance(flow_data_str, str) else flow_data_str
        for node in flow_data.get("nodes", []):
            node_data = node.get("data", {})
            nodes_summary.append(
                {
                    "id": node.get("id"),
                    "type": node_data.get("type", node.get("type", "Unknown")),
                    "label": node_data.get("label", node_data.get("name", "Unnamed")),
                    "category": node_data.get("category", "other"),
                }
            )
    except (json.JSONDecodeError, TypeError):
        pass

    simplified_flow = {
        "id": flow.get("id"),
        "name": flow.get("name"),
        "type": flow_type,
        "deployed": flow.get("deployed", False),
        "isPublic": flow.get("isPublic", False),
        "category": flow.get("category"),
        "createdDate": flow.get("createdDate"),
        "updatedDate": flow.get("updatedDate"),
        "nodes": nodes_summary,
    }

    if format_type == ResponseFormat.JSON:
        return json.dumps(simplified_flow, indent=2)

    lines = [
        f"# {type_indicator} {flow.get('name', 'Unnamed')}",
        "",
        f"**ID**: `{flow.get('id', 'N/A')}`",
        f"**Type**: {flow_type}",
        f"**Deployed**: {'Yes' if flow.get('deployed') else 'No'}",
        f"**Public**: {'Yes' if flow.get('isPublic') else 'No'}",
        f"**Created**: {flow.get('createdDate', 'N/A')}",
        f"**Updated**: {flow.get('updatedDate', 'N/A')}",
    ]

    if flow.get("category"):
        lines.append(f"**Categories**: {flow.get('category')}")

    if nodes_summary:
        lines.append("")
        lines.append("## Nodes")
        for node in nodes_summary:
            lines.append(f"- **{node['label']}** ({node['type']})")

    return "\n".join(lines)


def format_analysis(analysis: dict, format_type: ResponseFormat) -> str:
    """Format flow analysis for output."""
    if format_type == ResponseFormat.JSON:
        return json.dumps(analysis, indent=2)

    lines = [
        f"# Flow Analysis: {analysis['flow_name']}",
        "",
        f"**Type**: {analysis['flow_type']}",
        f"**Summary**: {analysis['summary']}",
        "",
    ]

    # Nodes overview
    if analysis["nodes"]:
        lines.append("## Nodes Overview")
        categories: dict[str, list[str]] = {}
        for node in analysis["nodes"]:
            cat = node["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(f"{node['label']} ({node['type']})")

        for cat, cat_nodes in sorted(categories.items()):
            lines.append(f"### {cat.replace('_', ' ').title()}")
            for n in cat_nodes:
                lines.append(f"- {n}")
        lines.append("")

    # Potential issues
    if analysis["potential_issues"]:
        lines.append("## [!] Potential Issues")
        for issue in analysis["potential_issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    # Improvement suggestions
    if analysis["suggestions"]:
        lines.append("## Improvement Suggestions")
        for suggestion in sorted(
            analysis["suggestions"], key=lambda x: 0 if x["priority"] == "high" else 1
        ):
            priority_indicator = "[HIGH]" if suggestion["priority"] == "high" else "[MEDIUM]"
            lines.append(f"### {priority_indicator} {suggestion['title']}")
            lines.append(f"**Category**: {suggestion['category']}")
            lines.append(f"\n{suggestion.get('description', '')}")

            if suggestion.get("tips"):
                lines.append("\n**Recommendations:**")
                for tip in suggestion["tips"]:
                    lines.append(f"- {tip}")

            if suggestion.get("nodes_to_add"):
                lines.append(f"\n**Suggested nodes**: {', '.join(suggestion['nodes_to_add'])}")
            lines.append("")

    # Best practices
    if analysis["best_practices"]:
        lines.append("## Best Practices")
        for practice in analysis["best_practices"]:
            lines.append(f"### {practice['title']}")
            if practice.get("tips"):
                for tip in practice["tips"]:
                    lines.append(f"- {tip}")
            lines.append("")

    return "\n".join(lines)


# =============================================================================
# Analyzers
# =============================================================================


def categorize_node(node_type: str) -> str:
    """Categorize a node type into a functional category."""
    node_lower = node_type.lower()

    categories = [
        (["llm", "gpt", "claude", "anthropic", "openai", "gemini", "mistral"], "llm"),
        (["memory", "buffer", "window"], "memory"),
        (["vector", "chroma", "pinecone", "faiss", "weaviate", "qdrant", "milvus"], "vector_store"),
        (["retriever", "retrieval"], "retriever"),
        (["loader", "document", "pdf", "csv"], "document_loader"),
        (["embed", "embedding"], "embeddings"),
        (["tool", "serp", "calculator", "request", "browser"], "tool"),
        (["prompt", "template"], "prompt"),
        (["agent", "supervisor", "worker"], "agent"),
        (["chain", "sequential"], "chain"),
        (["splitter", "chunk"], "text_splitter"),
        (["moderation"], "moderation"),
        (["cache"], "cache"),
        (["parser", "output"], "output_parser"),
    ]

    for keywords, category in categories:
        if any(kw in node_lower for kw in keywords):
            return category

    return "other"


def analyze_flow_data(flow: dict, improvement_goal: str | None = None) -> dict:
    """
    Analyze flow data and generate improvement suggestions.

    This function examines the flow configuration and provides actionable
    recommendations for improving the flow's performance and capabilities.
    """
    flow_type = flow.get("type", "CHATFLOW")
    analysis: dict = {
        "flow_name": flow.get("name", "Unknown"),
        "flow_type": flow_type,
        "summary": "",
        "nodes": [],
        "suggestions": [],
        "best_practices": [],
        "potential_issues": [],
    }

    flow_data_str = flow.get("flowData", "{}")
    try:
        flow_data = json.loads(flow_data_str) if isinstance(flow_data_str, str) else flow_data_str
    except (json.JSONDecodeError, TypeError):
        analysis["potential_issues"].append("Could not parse flow data - flow may be corrupted")
        return analysis

    nodes = flow_data.get("nodes", [])
    edges = flow_data.get("edges", [])

    categories_found: set[str] = set()
    for node in nodes:
        node_data = node.get("data", {})
        node_type = node_data.get("type", node_data.get("name", "Unknown"))
        node_label = node_data.get("label", node.get("id", "Unnamed"))

        category = categorize_node(node_type)
        categories_found.add(category)

        analysis["nodes"].append(
            {"id": node.get("id"), "type": node_type, "label": node_label, "category": category}
        )

    analysis["summary"] = f"Flow contains {len(nodes)} nodes and {len(edges)} connections."

    is_agent_flow = flow_type in ("AGENTFLOW", "MULTIAGENT")
    goal_lower = improvement_goal.lower() if improvement_goal else ""

    if "memory" not in categories_found:
        analysis["suggestions"].append(
            {
                "priority": "high",
                "category": "memory",
                "title": "Add Conversation Memory",
                "description": "This flow doesn't have memory nodes. Adding memory enables conversation context across messages.",
                "nodes_to_add": ["Buffer Memory", "Zep Memory", "Redis Memory", "MongoDB Memory"],
            }
        )

    if "knowledge" in goal_lower and "vector_store" not in categories_found:
        nodes_to_add = ["Chroma", "Pinecone", "FAISS", "OpenAI Embeddings"]
        if "document_loader" not in categories_found:
            nodes_to_add.extend(["PDF Loader", "Text Loader"])
        if "retriever" not in categories_found:
            nodes_to_add.append("Vector Store Retriever")
        analysis["suggestions"].append(
            {
                "priority": "high",
                "category": "rag",
                "title": "Add Vector Store for Knowledge Base",
                "description": "Add a Vector Store (Pinecone, Chroma, or FAISS) with Embeddings and Document Loaders for knowledge retrieval.",
                "nodes_to_add": nodes_to_add,
            }
        )

    if is_agent_flow and "tool" not in categories_found:
        analysis["suggestions"].append(
            {
                "priority": "medium",
                "category": "tools",
                "title": "Add Tools to Agent",
                "description": "This agent flow has no tools. Add tools to extend capabilities (Search, Calculator, API calls).",
                "nodes_to_add": ["SerpAPI", "Calculator", "Custom Tool", "Request Tool", "Web Browser"],
            }
        )

    if "format" in goal_lower and "output_parser" not in categories_found:
        analysis["suggestions"].append(
            {
                "priority": "medium",
                "category": "output",
                "title": "Add Output Parser",
                "description": "Add an Output Parser to structure responses (JSON, CSV, structured data).",
                "nodes_to_add": ["Structured Output Parser", "JSON Output Parser", "List Output Parser"],
            }
        )

    if "prompt" in categories_found:
        analysis["best_practices"].append(
            {
                "category": "prompts",
                "title": "Prompt Engineering Tips",
                "tips": [
                    "Use clear, specific instructions in your prompts",
                    "Include examples (few-shot learning) for better results",
                    "Define the output format explicitly",
                    "Use system prompts to set context and behavior",
                ],
            }
        )

    if flow.get("isPublic") and "moderation" not in categories_found:
        analysis["suggestions"].append(
            {
                "priority": "medium",
                "category": "safety",
                "title": "Add Input Moderation",
                "description": "This public flow lacks moderation. Add an Input Moderation node to filter inappropriate content.",
                "nodes_to_add": ["OpenAI Moderation", "Simple Prompt Moderation"],
            }
        )

    if "cache" not in categories_found:
        analysis["best_practices"].append(
            {
                "category": "performance",
                "title": "Consider Adding Caching",
                "tips": [
                    "Add a Cache node to store repeated LLM responses",
                    "Caching reduces costs and latency significantly",
                    "Redis Cache or In-Memory Cache are good options",
                ],
            }
        )

    if "accuracy" in goal_lower or "better" in goal_lower:
        analysis["suggestions"].append(
            {
                "priority": "high",
                "category": "accuracy",
                "title": "Improve Response Accuracy",
                "description": "To improve accuracy:",
                "tips": [
                    "Use a more capable model (GPT-4o, Claude 3.5 Sonnet)",
                    "Add relevant context through RAG",
                    "Improve prompts with clearer instructions",
                    "Add few-shot examples",
                    "Adjust temperature (lower for consistency, higher for creativity)",
                ],
            }
        )

    if "fast" in goal_lower or "speed" in goal_lower:
        analysis["suggestions"].append(
            {
                "priority": "high",
                "category": "performance",
                "title": "Improve Response Speed",
                "description": "To make responses faster:",
                "tips": [
                    "Use a faster model (GPT-4o-mini, Claude 3 Haiku)",
                    "Enable streaming for perceived faster responses",
                    "Add caching for repeated queries",
                    "Reduce context length where possible",
                    "Use smaller chunk sizes in RAG",
                ],
            }
        )

    if "handle" in goal_lower or "support" in goal_lower:
        analysis["suggestions"].append(
            {
                "priority": "medium",
                "category": "capability",
                "title": "Extend Capabilities",
                "description": f"Based on your goal '{improvement_goal}':",
                "tips": [
                    "Add specific tools for the functionality needed",
                    "Create custom tools using the Custom Tool node",
                    "Add relevant document sources via Document Loaders",
                    "Consider using Agent flows for complex multi-step tasks",
                    "Add conditional routing with Condition nodes",
                ],
            }
        )

    return analysis
