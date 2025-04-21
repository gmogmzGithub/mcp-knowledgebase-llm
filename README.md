# MCP Knowledge Base

A simple MCP client-server


## Requirements

- Python 3.9 or higher
- Poetry for dependency management
- OpenAI API key

## Setup

1. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

2Create a `.env` file in the project root or parent directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Project Structure

- `server.py`: MCP server implementation with tools
- `client-sse.py`: MCP client implementation with LLM capabilities
- `data/kb.json`: Knowledge base data with MCP-related Q&A
- `pyproject.toml`: Poetry configuration file

## Running the Application

1. Start the server:
   ```bash
   poetry run python server.py
   ```

2. In a separate terminal, run the client:
   ```bash
   poetry run python client-sse.py
   ```

## Using the Client

The client has two modes:

1. Direct tool calls:
   - Uncomment the `asyncio.run(test_direct_tool_calls())` line in `client-sse.py`
   - This directly calls the tools without using an LLM

2. LLM-powered interactions (default):
   - Uses OpenAI to interpret queries and call appropriate tools
   - Ask questions like "What is MCP?" or "What is the difference between stdio and SSE transports?"

## Customizing

- Add new tools to `server.py` by creating additional functions with the `@mcp.tool()` decorator
- Modify the knowledge base by updating `data/kb.json`
- Change the OpenAI model by modifying the `model` parameter in the `MCPClient` class

