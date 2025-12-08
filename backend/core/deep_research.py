import json
from openai import AsyncOpenAI
from core.mcp_client import *
from core.filter_data import filter_raw_html_data

client = AsyncOpenAI()

async def extract_idea_prd(cleaned_text: str) -> list:
    """
    Gọi LLM để phân tích cleaned_text và trích xuất danh sách các feature
    theo format yêu cầu của bảng Feature.
    
    Output:
    [
      {
        "title": "...",
        "user_story": "...",
        "business_value": "...",
        "priority_moscow": "Must/Should/Could/Wont"
      }
    ]
    """

    system_prompt = """
Bạn là một AI chuyên gia Product Owner.
Nhiệm vụ của bạn là đọc nội dung văn bản nghiên cứu thị trường và rút ra ý tưởng sản phẩm.
Mỗi ý tưởng phải được xuất ra dưới dạng một FEATURE.

Yêu cầu bắt buộc:
- Viết tiêu đề (title) ngắn gọn, rõ ràng.
- Viết user_story theo format: Là một [loại người dùng], tôi muốn [mục tiêu], để tôi có thể [lợi ích].
- Viết business_value: mô tả giá trị kinh doanh ngắn gọn (1–2 câu).
- Phân loại theo MoSCoW: Must / Should / Could / Wont.
- Không được giải thích ngoài format tren.
- Viet bang tieng Viet.

Chú ý:
- Chỉ dùng thông tin lấy từ tài liệu được cung cấp, không được bịa đặt thông tin
- Nếu tài liệu cung cấp không có thông tin gì, trả về mảng rỗng []
"""

    user_prompt = f"""
Dưới đây là cleaned_text đã thu thập từ nhiều URL:
{cleaned_text}
Hãy phân tích nội dung và rút trích danh sách các feature theo đúng format JSON như sau:

[
  {{
    "title": "string",
    "user_story": "As a [loại người dùng], I want to [mục tiêu], so that I can [lợi ích].",
    "business_value": "string",
    "priority_moscow": "Must/Should/Could/Wont"
  }}
]
"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    text = response.choices[0].message.content.strip()
    #print(f"\n[Extracted Features]\n{text}\n")
    return text

async def deep_research(user_input: str, limit: 3) -> list:
    """
    Phân tích user_input, tạo keyword tiếng Anh để search URL,
    gọi MCP tool search_url, và trả về list URLs.
    """
    results = []
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            #Goi tool search_url
            result_url = await session.call_tool("search_url", {"keyword": user_input, "limit": limit})

            #Trích xuất URLs từ content
            urls = []
            if hasattr(result_url, "content") and result_url.content:
                for item in result_url.content:
                    # item là TextContent(type="text", text="url")
                    if hasattr(item, "text"):
                        urls.append(item.text.strip())

            # print("[Deep Research] URLs found:")
            # for u in urls:
            #     print(" -", u)
                
            # Lặp qua từng URL, gọi tool fetch_raw_url và xử lý dữ liệu
            for url in urls:
                print(f"[Deep Research] Fetching raw HTML from {url}")

                try:
                    raw_result = await session.call_tool(
                        "fetch_raw_url",
                        {"url": url}
                    )
                except Exception as e:
                    print(f"Error fetching {url}: {e}")
                    continue

                # raw_result.content = list[TextContent]
                if not raw_result.content:
                    continue

                raw_html = ""
                item = raw_result.content[0]
                if hasattr(item, "text"):
                    raw_html = item.text

                #Clean HTML → text
                cleaned_text = filter_raw_html_data(raw_html)
                
                #Get ideas
                ideas = await extract_idea_prd(cleaned_text)

                results.append({
                    "url": url,
                    "text": cleaned_text,
                    "idea": ideas
                })
                
                
                # print(f"Url: {url} - Text length: {len(cleaned_text)} characters\n----------------------------------\n")
                # print(f"Cleaned text preview: {cleaned_text[:2000]}...\n-------------------\n\n\n")
                # print(f"Ideas extracted: {ideas}\n============================\n\n")
            
            # Merge all ideas
            merged_chunks = []
            for item in results:
                idea_text = item.get("idea", "")
                if isinstance(idea_text, str) and idea_text.strip():
                    merged_chunks.append(idea_text.strip())

            # Ghép lại bằng 2 dòng trống để LLM dễ phân tách
            final_deep_research_output = "\n\n".join(merged_chunks)
            print(f"\n[Final Deep Research Output]\n{final_deep_research_output}\n")
            return final_deep_research_output
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(deep_research("ung dung quan ly thoi gian su dung mang xa hoi", None))