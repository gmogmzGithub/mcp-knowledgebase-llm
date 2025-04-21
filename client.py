import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(".env")

"""
Make sure:
1. The server is running before running this script.
2. The server is configured to use SSE transport.
3. The server is listening on port 8050.

To run the server:
python server.py
"""


class MCPClient:
    """Client for interacting with OpenAI models using MCP tools."""

    def __init__(self, model: str = "gpt-4o"):
        """Initialize the OpenAI MCP client.

        Args:
            model: The OpenAI model to use.
        """
        self.session = None
        self.openai_client = AsyncOpenAI()
        self.model = model
        self.read_stream = None
        self.write_stream = None

    async def connect_to_server(self):
        """Connect to an MCP server using SSE transport."""
        # Connect to the server using SSE
        self.read_stream, self.write_stream = await sse_client("http://localhost:8050/sse")
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.initialize()

        # List available tools
        tools_result = await self.session.list_tools()
        print("\nConnected to server with tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")

        return tools_result.tools

    async def get_mcp_tools(self):
        """Get available tools from the MCP server in OpenAI format."""
        tools_result = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_result.tools
        ]

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available MCP tools.

        Args:
            query: The user query.

        Returns:
            The response from OpenAI.
        """
        # Get available tools
        tools = await self.get_mcp_tools()

        # Initial OpenAI API call
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )

        # Get assistant's response
        assistant_message = response.choices[0].message

        # Initialize conversation with user query and assistant response
        messages = [
            {"role": "user", "content": query},
            assistant_message,
        ]

        # Handle tool calls if present
        if assistant_message.tool_calls:
            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                # Execute tool call
                result = await self.session.call_tool(
                    tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments),
                )

                # Add tool response to conversation
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content[0].text,
                    }
                )

            # Get final response from OpenAI with tool results
            final_response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="none",  # Don't allow more tool calls
            )

            return final_response.choices[0].message.content

        # No tool calls, just return the direct response
        return assistant_message.content

    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.aclose()
        if self.read_stream:
            await self.read_stream.aclose()
        if self.write_stream:
            await self.write_stream.aclose()


async def test_direct_tool_calls():
    """Test direct tool calls without LLM."""
    async with sse_client("http://localhost:8050/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Call our multiplication tool
            result = await session.call_tool("multiply", arguments={"a": 6, "b": 7})
            print(f"6 × 7 = {result.content[0].text}")

            # Call the knowledge base tool
            kb_result = await session.call_tool("get_knowledge_base")
            print(f"Knowledge Base Sample (first 200 chars):\n{kb_result.content[0].text[:200]}...")


async def main():
    """Main entry point for the client using LLM capabilities."""
    client = MCPClient()
    await client.connect_to_server()

    # Example queries to test the tools with LLM
    queries = [
        "What is 6 multiplied by 7?",
        "What is our company's vacation policy?",
        "How many days of remote work are allowed per week according to our policy?"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        response = await client.process_query(query)
        print(f"Response: {response}")
        print("-" * 50)

    await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())