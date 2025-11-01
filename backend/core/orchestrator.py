import os, json, re
from openai import OpenAI
from dotenv import load_dotenv
from backend.core.summarizer import get_latest_summary

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ai_orchestrator(user_prompt, section_id, chat_history, BUFFER_SIZE=5):
    """
    AI Orchestrator — phân loại intent của người dùng có xét context gần nhất.
    Output:
      - {"route": "call_mcp"}
      - {"route": "PRD_related_answer"}
      - {"route": "direct_answer", "content": "..."}
    """
    latest_summary = get_latest_summary(section_id)

    system_prompt = """
    Bạn là AI điều phối (AI Orchestrator). 
    Nhiệm vụ: xác định loại yêu cầu của người dùng dựa vào context hiện tại.

    Context này mô tả các trao đổi trước đó trong cùng hội thoại.
    Dựa trên context và câu hỏi hiện tại, hãy phân loại yêu cầu.

    Có 3 loại output hợp lệ, trả về duy nhất một dòng JSON:
    {"route": "call_mcp"}  
      --> nếu câu hỏi cần gọi tool bên ngoài để lấy dữ liệu (ví dụ: tra cứu, thời tiết, bóng đá, tin tức,...)

    {"route": "PRD_related_answer"}  
      --> nếu câu hỏi liên quan đến viết, chỉnh sửa, mở rộng hoặc hỏi về PRD / sản phẩm.

    {"route": "direct_answer", "content": "..."}  
      --> nếu chỉ cần trả lời ngắn trực tiếp, không cần tool và không liên quan PRD.

    Trả về đúng JSON, không thêm lời giải thích.
    """

    # ===== Chuẩn bị context =====
    context_info = ""
    if latest_summary:
        context_info += f"Context tóm tắt trước đó:\n{latest_summary}\n\n"
    if chat_history:
        context_info += "Các lượt hội thoại gần nhất:\n"
        for u, a in chat_history[-BUFFER_SIZE:]:
            context_info += f"User: {u}\nAssistant: {a}\n"

    user_prompt_full = f"{context_info}\n\nCâu hỏi mới của người dùng:\n{user_prompt}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_full},
        ],
        temperature=0,
        max_tokens=200,
    )

    text = response.choices[0].message.content.strip()
    print(f"\n[AI ORCHESTRATOR OUTPUT]\n{text}\n")

    try:
        # Bóc JSON an toàn
        match = re.search(r"\{.*\}", text)
        if not match:
            return {"route": "direct_answer", "content": text}
        data = json.loads(match.group(0))
        return data
    except Exception:
        return {"route": "direct_answer", "content": text}