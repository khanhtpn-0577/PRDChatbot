from openai import OpenAI
from core.mcp_client import *
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def mcp_integration(user_prompt):
    """
    Chatbot 2: MCP Bot xử lý gọi tool và tổng hợp dữ liệu.
    - Gọi tool cần thiết từ MCP.
    - Tổng hợp kết quả.
    - Tóm tắt lại bằng LLM trước khi gửi về chatbot chính.
    """
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await get_available_tools(session)
            functions = [conver_to_llm_tool(t) for t in tools]

            # --- B1: Dùng LLM để quyết định tool nào cần gọi ---
            tool_calls = await call_llm(user_prompt, functions)
            if not tool_calls:
                return None  # Không cần tool

            # --- B2: Gọi tool qua MCP ---
            combined_result = ""
            for t in tool_calls:
                print(f"Calling MCP Tool: {t['name']} with args {t['args']}")
                result = await session.call_tool(t["name"], t["args"])
                combined_result += f"\n[{t['name']} Result]\n{result}"

            # --- B3: Dùng LLM tóm tắt kết quả MCP ---
            print("\n[Combined MCP Result]\n", combined_result)
            summary_prompt = f"""
Bạn là một trợ lý AI.
Dưới đây là kết quả thô từ các công cụ MCP cho querry của người dùng:

{user_prompt}

Kết quả MCP:

{combined_result}

Hãy tóm tắt lại thông tin quan trọng, trình bày ngắn gọn, dễ hiểu bằng tiếng Việt.
Nếu có nhiều kết quả từ nhiều công cụ, hãy gộp chúng thành 1 bản tóm tắt logic, chỉ giữ lại ý chính.
Trả về đoạn văn tóm tắt (không liệt kê, không bullet points).
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.2,
                max_tokens=400,
            )
            summarized_result = response.choices[0].message.content.strip()

            print("\n[Summarized MCP Result]\n", summarized_result)
            return summarized_result