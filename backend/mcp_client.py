import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_SERVER_URL = "https://81ac0c486085.ngrok-free.app/mcp"

async def get_available_tools(session):
    """
    Lấy danh sách tool từ MCP session.
    Trả về list dict [{name, description, inputSchema, outputSchema}]
    """
    meta, nextCursor, tools_tuple = await session.list_tools()

    # tools_tuple có dạng: ('tools', [Tool(...), Tool(...), ...])
    if isinstance(tools_tuple, tuple) and len(tools_tuple) == 2:
        tools_list = tools_tuple[1]
    else:
        tools_list = tools_tuple

    available_tools = []
    for t in tools_list:
        # Nếu t là object Tool (pydantic/dataclass) → lấy attr
        if hasattr(t, "model_dump"):  # pydantic v2
            t_dict = t.model_dump()
        elif hasattr(t, "dict"):      # pydantic v1
            t_dict = t.dict()
        else:                         # fallback
            t_dict = t.__dict__

        tool_info = {
            "name": t_dict.get("name"),
            "description": t_dict.get("description"),
            "inputSchema": t_dict.get("inputSchema"),
            "outputSchema": t_dict.get("outputSchema"),
        }
        available_tools.append(tool_info)

    return available_tools

async def test():
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            tools = await get_available_tools(session)
            for tool in tools:
                print(f"- {tool['name']}: {tool['description']}, {tool['inputSchema']}, {tool['outputSchema']}")

async def test2():
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            result = await session.call_tool(
                "web_search",
                {"query": "Artificial Intelligence", "limit": 2}
            )
            print("Web Search Results:")
            for item in result:
                print(item)
asyncio.run(test2())
        