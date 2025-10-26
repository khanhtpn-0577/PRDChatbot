from openai import OpenAI
from dotenv import load_dotenv
import os
import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_models import Section, ContextItem, Base
from transformers import pipeline
from mcp_client import *

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)



chat_history = []
CHAT_THREADHOLD = 5
BUFFER_SIZE = CHAT_THREADHOLD

'''
DOCS:
- Summarize (5 lần chat ping pong mới nhất + context gần nhất) --> lưu vào db: get_lattest_summary --> summarize_and_update-->save_summary
- Query = Context gần nhất +User input: get_lattest_summary -->complete user prompt --> call model
'''

'''
- Cải tiến:
+ Thêm buffer memory hỗ trợ trả lời các câu hỏi trong cùng 1 batch(chưa summarize)
+ Thêm model open source cho tác vụ summarize --> giảm chi phí --> toàn model tệ
'''

# ============ AI ORCHESTRATOR ==================
# ===============================================
def ai_orchestrator(user_prompt, section_id):
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


def save_summary(section_id, summary_text):
    with SessionLocal() as db:
        latest = (
            db.query(ContextItem)
            .filter(ContextItem.section_id == section_id)
            .order_by(ContextItem.version.desc())
            .first()
        )
        new_version = 1 if latest is None else latest.version + 1
        
        item = ContextItem(
            section_id = section_id,
            summary_text=summary_text,
            version=new_version
        )
        db.add(item)
        db.commit()
        
def get_latest_summary(section_id):
    with SessionLocal() as db:
        latest = (
            db.query(ContextItem)
            .filter(ContextItem.section_id == section_id)
            .order_by(ContextItem.version.desc())
            .first()
        )
        return latest.summary_text if latest else None
    
#model open source cho tac vu summarize
#summarizer = pipeline("summarization", model="VietAI/vit5-base",tokenizer="VietAI/vit5-base", device=0)
def summarize_and_update(section_id):
    latest_summary = get_latest_summary(section_id)
    recent_chat = "\n".join(
        [f"User:{u}\nAssistan: {a}" for u, a in chat_history[-CHAT_THREADHOLD:]]
    )
    
    if latest_summary:
        conversation_text = (
            f"Context summary trước đó:\n{latest_summary}\n\n"
            f"Đoạn hội thoại mới:\n{recent_chat}"
        )
    else:
        conversation_text = f"Đoạn hội thoại mới:\n{recent_chat}"
        
    system_prompt = """
    Tóm tắt hội thoại sau thành 1 context ngắn gọn,
    giữ lại các quyết định, yêu cầu, constraint quan trọng.
    Output: bullet points.
    """
    # input_text = f"{system_prompt}\n\n{conversation_text}"
    # summary = summarizer(input_text, max_length=500, min_length=50, do_sample=False)
    # summary_text = summary[0]['summary_text']
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation_text},
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    summary_text = response.choices[0].message.content.strip()
    save_summary(section_id, summary_text)
    
    return summary_text

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

async def prd_chatbot(section_id, user_input):
    latest_summary = get_latest_summary(section_id)
    system_prompt = '''Bạn là một chuyên gia viết Product Requirements Document (PRD) chuyên nghiệp.
Nhiệm vụ của bạn là tạo ra tài liệu yêu cầu sản phẩm (PRD) hoàn chỉnh dựa trên một câu truy vấn (query) mô tả yêu cầu hoặc ý tưởng ứng dụng.

Mục tiêu: Sinh ra PRD chuẩn kỹ thuật, có cấu trúc rõ ràng, ngắn gọn, và bám sát yêu cầu.
PRD phải tuân thủ cú pháp Markdown theo đúng mẫu bên dưới.

Cú pháp bắt buộc:
# Requirements Document

## Introduction
[Mô tả ngắn gọn về mục tiêu, đối tượng người dùng và giá trị của ứng dụng. Viết 3–6 câu, bằng tiếng Việt tự nhiên, giọng formal, không liệt kê.]

## Requirements

### Requirement 1
**User Story:** [Viết 1 câu mô tả hành vi hoặc mục tiêu của người dùng cuối, dạng "Là một [người dùng], tôi muốn [hành động] để [mục đích]".]

#### Acceptance Criteria
1. WHEN ... THEN ... SHALL ...
2. WHEN ... THEN ... SHALL ...
3. WHEN ... THEN ... SHALL ...
4. IF ... THEN ... SHALL ...
[Có thể thêm 1–2 dòng nếu cần, nhưng tối thiểu 4 ý. Mỗi dòng bắt đầu bằng WHEN hoặc IF, viết bằng tiếng Việt.]

### Requirement 2
**User Story:**

#### Acceptance Criteria
1. WHEN ... THEN ... SHALL ...
2. WHEN ... THEN ... SHALL ...
3. WHEN ... THEN ... SHALL ...
4. IF ... THEN ... SHALL ...

### Requirement 3
**User Story:**

#### Acceptance Criteria
1. WHEN ... THEN ... SHALL ...
2. WHEN ... THEN ... SHALL ...
3. WHEN ... THEN ... SHALL ...
4. IF ... THEN ... SHALL ...

...

Quy tắc nội dung:
Luôn sinh ít nhất 1 Requirement (hoặc nhiều hơn nếu query phức tạp).

Không giải thích thêm ngoài PRD, không thêm tiêu đề khác ngoài format trên.

Không thêm ký tự đặc biệt, dấu code block, hoặc markdown thừa ngoài cú pháp.

Viết toàn bộ bằng tiếng Việt.

Trong phần “Acceptance Criteria”, phải luôn có ít nhất 4 điều kiện logic dạng:

“WHEN người dùng [hành động] THEN hệ thống SHALL [kết quả]”

“IF [điều kiện] THEN hệ thống SHALL [hành động]”

Có thể trộn WHEN/IF để đa dạng.

Giữ tone chuyên nghiệp, dễ hiểu, và dùng từ đúng ngành (UX, dữ liệu, quản lý, bảo mật, hiệu năng… nếu phù hợp).


Ví dụ đầu vào:
Input: “Viết PRD cho ứng dụng giúp sinh viên quản lý thời gian học và làm thêm.”
Output:
# Requirements Document

## Introduction
Ứng dụng quản lý thời gian học tập và làm thêm giúp sinh viên tổ chức lịch học, công việc và nghỉ ngơi một cách hiệu quả. Ứng dụng này hỗ trợ cân bằng giữa học tập và thu nhập, giúp giảm stress và cải thiện hiệu suất cá nhân.

## Requirements

### Requirement 1
**User Story:** Là một sinh viên, tôi muốn quản lý thời gian biểu học và làm thêm, để tôi không bị trùng lịch và đảm bảo thời gian nghỉ ngơi.

#### Acceptance Criteria
1. WHEN người dùng thêm buổi học hoặc ca làm THEN hệ thống SHALL kiểm tra xung đột thời gian và cảnh báo nếu có trùng lịch.
2. WHEN người dùng hoàn tất tuần học THEN hệ thống SHALL hiển thị thống kê thời gian học, làm và nghỉ.
3. IF người dùng có lịch dày đặc THEN hệ thống SHALL gợi ý giảm tải hoặc sắp xếp lại thứ tự ưu tiên.
4. WHEN người dùng thay đổi lịch học THEN hệ thống SHALL đồng bộ thông tin với lịch tổng và gửi thông báo nhắc nhở.'''
    if latest_summary:
        system_prompt +=(
            "\n\nĐây là tóm tắt context trước đó, hãy dùng để trả lời nhất quán:\n"
            f"{latest_summary}"
        )
        
    # buffer N lượt chat gần nhất
    buffer_msgs = []
    for u, a in chat_history[-BUFFER_SIZE:]: 
        buffer_msgs.append({"role":"user", "content": u})
        buffer_msgs.append({"role":"assistant", "content": a})
    
    messages = [{"role":"system", "content":system_prompt}] + buffer_msgs + [{"role":"user", "content": user_input}]
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
    )
    bot_reply = response.choices[0].message.content
    
    print(f"\n\n========================\n\nContext: {messages}\n\n========================\n\n")
        
    return bot_reply

def create_section(name: str):
    with SessionLocal() as db:
        section = db.query(Section).filter(Section.section_name == name).first()

        if section:
            return section.section_id

        new_section = Section(section_name=name)
        db.add(new_section)
        db.commit()
        db.refresh(new_section)
        return new_section.section_id

# ============ MAIN CHAT LOOP ===================
async def run_chat():
    section_id = create_section("mcp-orchestrated-test-v3")
    print(f"Created section: {section_id}\n")

    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Closing...")
            break

        # ======= GỌI ORCHESTRATOR =======
        route_info = ai_orchestrator(user_input, section_id)
        route = (route_info.get("route") or "").strip()

        if route == "call_mcp":
            print("Đang gọi MCP để lấy dữ liệu...\n")
            mcp_data = await mcp_integration(user_input)
            if mcp_data:
                enriched_input = f"{user_input}\n\n[Dữ liệu MCP thu thập được:]\n{mcp_data}"
                reply = await prd_chatbot(section_id, enriched_input)
            else:
                reply = "Không tìm thấy dữ liệu phù hợp từ MCP."
            # Lưu lịch sử
            chat_history.append((user_input, reply))

        elif route == "PRD_related_answer":
            reply = await prd_chatbot(section_id, user_input)
            chat_history.append((user_input, reply))

        elif route == "direct_answer":
            reply = route_info.get("content", "").strip() or "Đã nhận yêu cầu của bạn."
            # Lưu lịch sử cho thống nhất
            chat_history.append((user_input, reply))

        else:
            # Fallback: không nhận diện được route → coi như trả lời trực tiếp
            reply = route_info.get("content", "Xin lỗi, tôi chưa hiểu yêu cầu của bạn.")
            chat_history.append((user_input, reply))

        # Chu kỳ tóm tắt ngữ cảnh
        if len(chat_history) % CHAT_THREADHOLD == 0:
            summary = summarize_and_update(section_id)
            print("\n[CONTEXT UPDATED]\n", summary)

        print(f"\nBot: {reply}\n" + "-" * 90 + "\n\n")

        
if __name__ == "__main__":
    asyncio.run(run_chat())
    
    

