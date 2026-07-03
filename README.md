# 🛠️ MCP Token Optimizer: Smart Context Pruning Server

[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard-blue.svg?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-darkgreen.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

An open-source **Model Context Protocol (MCP)** server designed to expose context-optimization and token-saving utilities to AI agents (like Claude Desktop, Cursor, or Gemini). 

By offering structured tools for **semantic context pruning** and **caching boundary alignment**, this server significantly decreases API billing overhead and latency.

---

## 💡 The Problem: Prompt Cache Invalidation & Token Waste

Most modern LLM APIs (Anthropic, Gemini, OpenAI) support **Prompt Caching** (or Context Caching) which makes processing long developer prompts up to **90% cheaper and 10x faster**. However, prompt caching has strict rules:
1. **Identical Prefixes**: The prefix of the prompt must be *100% identical* to hit the cache. If your chat history or files change slightly at the beginning, the entire cache is invalidated.
2. **Block Boundaries (1024 Tokens)**: Prompts are cached in blocks of 1024 tokens. If your prompt size is 1030 tokens, it allocates 2 full blocks (2048 tokens), billing you for 1018 unused tokens.
3. **Log & Trace Bloat**: Raw terminal outputs, stack traces, and system files contain immense boilerplate (repeated timestamps, standard paths, redundant logs) that waste costly tokens.

This server solves these problems programmatically.

---

## ⚙️ Features & Tools

This server exposes two highly optimized tools:

### 1. `prune_context`
- **Purpose**: Cleans up logs, traces, or large documents before injecting them into the LLM context.
- **Operations**:
  - Removes duplicate lines.
  - Automatically strips heavy timestamp headers (e.g., ISO-8601 strings) and log-level boilerplate.
  - Performs keyword-focused context extraction (keeps lines surrounding target keywords and filters out the rest).
  - Truncates redundant middle sections of large log streams.

### 2. `align_prompt_cache`
- **Purpose**: Pads context strings to fit exact 1024-token cache blocks.
- **Operations**:
  - Estimates current token count.
  - Calculates the nearest 1024-token boundary (e.g., 2048, 3072).
  - Pads the context with neutral comment spaces to align it exactly to the block boundary, stabilizing the prompt prefix and ensuring high cache hit ratios.

---

## 📁 Project Directory Structure
```
mcp-token-optimizer/
├── README.md               # Technical system manual (this file)
├── requirements.txt        # Core dependencies
└── mcp_server.py           # FastMCP server code implementing tools
```

---

## 🚀 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure with Claude Desktop
To add this optimizer server to your Claude Desktop config, modify your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "token-optimizer": {
      "command": "python",
      "args": ["C:/Users/risha/.gemini/antigravity/scratch/mcp-token-optimizer/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop, and the agent will automatically use these tools to optimize its inputs!
