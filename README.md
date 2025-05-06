[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

# INE-MCP. MCP Integration with INE API

**INE is Spain's National Statistics Institute.**

**INE-mcp** allows access to official Spanish statistical data directly from Claude AI and other compatible MCP clients using the **Model Context Protocol (MCP)**.

INE-mcp is an MCP server that exposes tools for LLMs to query economic, demographic and social indicators from INE.

## Key Features

- **Economic indicators** query (GDP, CPI, unemployment, etc.)
- Access to **demographic data** (census, migrations, birth rates)
- Historical time series of statistical data
- Metadata of official statistical operations
- Filtering by territory, period and specific variables
- Structured responses in JSON format

## Installation

### Install from uv

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### uv Installation

First install `uv`, a Python package manager.  
**Install from terminal:**

For Mac and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For Windows:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Alternatively install with pip:

```bash
pip install uv
```

For more details about **uv** installation, see [official documentation](https://docs.astral.sh/uv/getting-started/installation/).

## Integration with Desktop Clients like Claude

Once **uv** is installed, you can use the MCP server from any compatible client like Claude Desktop by following these steps:

1. Go to **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**
2. Add this code block under `"mcpServers"`:

```json
"ine_mcp": {
    "command": "uvx",
    "args": [
        "ine_mcp"
    ]
}   
```

3. Consult INE's official documentation: <https://www.ine.es/dyngs/DAB/index.htm?cid=1099>
4. If you have other MCP servers configured, separate them with commas `,`.

For integration with other MCP-compatible clients like Cursor, CODEGPT or Roo Code, simply add the same code block to the client's MCP server configuration.

## Usage Examples

Once properly configured, you can ask things like:

```
- "What data from Spain's INE can you access?"
- "Find data from the Active Population Survey (EPA)"
- "Show me price indices for steel products during Q1 2023"
---
