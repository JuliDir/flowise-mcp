# Flowise MCP Server

[![PyPI version](https://badge.fury.io/py/flowise-mcp.svg)](https://pypi.org/project/flowise-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)
[![Flowise](https://img.shields.io/badge/Flowise-API-purple.svg)](https://flowiseai.com/)

An MCP (Model Context Protocol) server that enables AI agents to interact with [Flowise](https://flowiseai.com/) instances. Works with Claude Desktop, VS Code GitHub Copilot, Cursor, and other MCP-compatible clients.

## Features

- **Flow Management**: List, create, update, and delete chatflows and agentflows
- **Predictions**: Send messages to flows and receive responses
- **Flow Analysis**: Analyze configurations with improvement suggestions
- **Assistants**: List and inspect Flowise assistants
- **Document Stores**: Manage document stores for RAG
- **Vector Operations**: Upsert vectors and query vector stores
- **Chat History**: Retrieve and delete conversation history
- **Variables & Tools**: Manage global variables and tools

## Requirements

- Python 3.10+ or [uv](https://docs.astral.sh/uv/) package manager
- A running Flowise instance with API access

## Installation

### Option A: Using pip

```bash
pip install flowise-mcp
```

### Option B: Using uv (recommended)

```bash
# Install uv first if you don't have it
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then configure your AI client to use `uvx flowise-mcp` (see below).

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FLOWISE_BASE_URL` | Your Flowise instance URL | Yes |
| `FLOWISE_API_KEY` | API key for authentication | Yes |
| `FLOWISE_TIMEOUT` | Request timeout in seconds (default: 60) | No |

### Getting your Flowise API Key

1. Open your Flowise instance
2. Go to Settings > API Keys
3. Create a new API key or copy an existing one

## Setup by Client

### VS Code (GitHub Copilot)

Requires VS Code 1.99+ with GitHub Copilot.

Add to `.vscode/mcp.json` in your project or to your User Settings (JSON):

```json
{
  "servers": {
    "flowise": {
      "command": "uvx",
      "args": ["flowise-mcp"],
      "env": {
        "FLOWISE_BASE_URL": "https://your-flowise-instance.com",
        "FLOWISE_API_KEY": "your-api-key"
      }
    }
  }
}
```

Restart VS Code after adding the configuration.

### Claude Desktop

Add to your config file:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "flowise": {
      "command": "uvx",
      "args": ["flowise-mcp"],
      "env": {
        "FLOWISE_BASE_URL": "https://your-flowise-instance.com",
        "FLOWISE_API_KEY": "your-api-key"
      }
    }
  }
}
```

Restart Claude Desktop after adding the configuration.

## Available Tools

### Flow Management

| Tool | Description |
|------|-------------|
| `flowise_list_flows` | List all chatflows and agentflows |
| `flowise_get_flow` | Get detailed flow configuration |
| `flowise_create_flow` | Create a new flow |
| `flowise_update_flow` | Update an existing flow |
| `flowise_delete_flow` | Delete a flow |
| `flowise_predict` | Send a message to a flow |
| `flowise_analyze_flow` | Analyze flow and get improvement suggestions |

### Assistants

| Tool | Description |
|------|-------------|
| `flowise_list_assistants` | List all configured assistants |
| `flowise_get_assistant` | Get assistant details and configuration |

### Document Stores & Vectors

| Tool | Description |
|------|-------------|
| `flowise_list_document_stores` | List all document stores |
| `flowise_get_document_store` | Get document store details |
| `flowise_upsert_vector` | Insert/update vectors in a flow |
| `flowise_query_vector_store` | Search documents in a vector store |

### Chat & Configuration

| Tool | Description |
|------|-------------|
| `flowise_get_chat_history` | Get conversation history |
| `flowise_delete_chat_history` | Delete conversation history |
| `flowise_list_variables` | List global variables |
| `flowise_list_tools` | List available tools |
| `flowise_ping` | Check server connectivity |

## Usage Examples

```
"List all my agentflows"

"Send 'Hello' to flow abc123"

"Analyze flow xyz789 and suggest improvements for better accuracy"

"Create a new chatflow named 'Customer Support Bot'"

"Show me all document stores"

"Query the vector store for 'pricing information'"

"Delete chat history for flow abc123"

"List all assistants"
```

## Development

If you want to contribute or run locally:

```bash
git clone https://github.com/JuliDir/flowise-mcp.git
cd flowise-mcp

# Using uv
uv sync --extra dev
uv run pytest

# Or using pip
pip install -e ".[dev]"
pytest
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not appearing | Restart your AI client |
| `uvx` not found | Install uv (see step 1) |
| Connection error | Check `FLOWISE_BASE_URL` |
| Authentication failed | Verify `FLOWISE_API_KEY` |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Julian Di Rocco ([@JuliDir](https://github.com/JuliDir))
