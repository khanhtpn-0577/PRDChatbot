import asyncio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import re

##MCP Server URL
MCP_SERVER_URL = "https://e1b1b156ddbb.ngrok-free.app/mcp"

##LLM CONFIG
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def conver_to_llm_tool(tool_dict):
    """
    Chuyển dict tool sang object LLMTool
    """
    return {
        "type": "function",
        "function":{
            "name": tool_dict["name"],
            "description": tool_dict["description"],
            "parameters": tool_dict.get("inputSchema", {}),
        }
    }
    
async def call_llm(prompt, functions):
    """
    Gọi LLM để quyết định tool nào cần gọi dựa trên prompt và danh sách functions (tools).
    """
    tool_list = [
        {
            "name": f["function"]["name"],
            "description": f["function"]["description"],
            "inputSchema": f["function"]["parameters"],
        }
        for f in functions
    ]
    
    system_prompt = (
        "You are an AI orchestrator. You can call one of the following tools. "
        "Respond strictly in format: "
        "[{\"name\": <tool_name>, \"args\": {<key>: <value>}}]"
    )
    
    full_prompt = f"{system_prompt}\n\nAvailable tools: {json.dumps(tool_list, indent=2)}\n\nUser prompt: {prompt}"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": full_prompt},
        ],
        temperature=0,
        max_tokens=500
    )
    response_text = response.choices[0].message.content.strip()
    print("\n[Raw LLM Response]\n", response_text)
    
    if response_text.startswith("```"):
        # xóa phần mở và đóng ```json ... ```
        response_text = re.sub(r"^```[a-zA-Z0-9]*\n?", "", response_text)
        response_text = re.sub(r"```$", "", response_text)
        response_text = response_text.strip()
    
    try:
        tool_calls = json.loads(response_text)
    except Exception as e:
        print("JSON parse error:", e)
        print("Raw response text:\n", response_text)
        tool_calls = []
    
    return tool_calls


##Test navigation with MCP tools
async def test_navigate(prompt:str):
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await get_available_tools(session)
            print("Available tools:", [t["name"] for t in tools])
            
            functions = [conver_to_llm_tool(t) for t in tools]
            
            print(f"\n LLM deciding tool for promt: '{prompt}'")
            funtions_to_call = await call_llm(prompt, functions)
            print("\n[LLM Decided Tool Calls]\n", funtions_to_call)
            
            for t in funtions_to_call:
                print(f"\nCalling tool: {t['name']} with args: {t['args']}")
                resutl = await session.call_tool(t['name'], t['args'])
                print(f"Tool Result:\n{resutl}")


if __name__ == "__main__":
    prompt = "lịch thi đấu bóng đá c1 ngày 21/10/2025"
    asyncio.run(test_navigate(prompt))
