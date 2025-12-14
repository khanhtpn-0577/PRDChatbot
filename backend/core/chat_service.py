# core/chat_service.py

from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import asc
import json

from db.db_models import Section, Message  # Message là model anh mới thêm
from core.orchestrator import ai_orchestrator
from core.mcp_integration import mcp_integration
from core.prd_agent import prd_chatbot
from core.prd_storage import save_prd, extract_prd_text
from core.summarizer import summarize_and_update

CHAT_THRESHOLD = 5
BUFFER_SIZE = CHAT_THRESHOLD


# ====== Helper thao tác DB ======

def create_section(db: Session, name: Optional[str] = None) -> UUID:
    """Tạo section mới (session mới) nếu chưa có."""
    section_name = name or "web-session"
    section = Section(section_name=section_name)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section.section_id


def save_message(db: Session, section_id: UUID, role: str, content: str) -> None:
    """Lưu 1 message vào bảng messages."""
    if isinstance(content, (dict, list)):
        content = json.dumps(content, ensure_ascii=False)
    msg = Message(
        section_id=section_id,
        role=role,         # "user" | "assistant"
        content=content,
    )
    db.add(msg)
    db.commit()


def load_chat_history(db: Session, section_id: UUID) -> List[Tuple[str, str]]:
    """
    Lấy lịch sử chat từ DB và chuyển thành dạng list[(user, assistant)] 
    để tái sử dụng cho ai_orchestrator / summarize_and_update.
    """
    messages = (
        db.query(Message)
        .filter(Message.section_id == section_id)
        .order_by(asc(Message.created_at))
        .all()
    )

    chat_history: List[Tuple[str, str]] = []
    pending_user: Optional[str] = None

    for m in messages:
        if m.role == "user":
            pending_user = m.content
        elif m.role == "assistant" and pending_user is not None:
            chat_history.append((pending_user, m.content))
            pending_user = None

    return chat_history


# ====== Core logic xử lý 1 lượt message từ user ======

async def process_user_message(
    db: Session,
    section_id: UUID,
    user_input: str,
) -> str:
    """
    Xử lý 1 lượt chat:
    - Lấy history từ DB
    - Orchestrate route
    - Gọi MCP / PRD agent
    - Extract & save PRD nếu có
    - Lưu message user + bot vào DB
    - Tóm tắt context nếu đủ ngưỡng
    - Trả về reply (string) cho API
    """

    # Lịch sử trước lượt này (từ DB)
    chat_history = load_chat_history(db, section_id)

    # ======= ROUTER =======
    route_info = ai_orchestrator(
        user_input,
        section_id,
        chat_history,
        BUFFER_SIZE=BUFFER_SIZE
    )
    route = (route_info.get("route") or "").strip()

    # ======= XỬ LÝ THEO ROUTE =======
    if route == "call_mcp":
        # mcp_data = await mcp_integration(user_input)
        # if mcp_data:
        #     enriched_input = (
        #         f"{user_input}\n\n[Dữ liệu MCP thu thập được:]\n{mcp_data}"
        #     )
        #     reply = await prd_chatbot(
        #         section_id,
        #         enriched_input,
        #         chat_history=chat_history,
        #         is_deep_research=0,
        #         BUFFER_SIZE=BUFFER_SIZE,
        #     )

        #     # extract prd
        #     extraction = extract_prd_text(reply)
        #     if extraction.get("is_prd"):
        #         prd_content = extraction.get("prd_content", "").strip()
        #         if prd_content.startswith("# Requirements Document"):
        #             save_prd(section_id, prd_content)
        #         # else: có thể log lại nếu format không đúng
        # else:
        #     reply = "Không tìm thấy dữ liệu phù hợp từ MCP."
        #Tam tat tinh nang mcp
        reply_string = route_info.get("content", "").strip() or "Đã nhận yêu cầu của bạn."
        reply = {
            "flag": "normal",
            "message": reply_string
        }
    elif route == "PRD_related_answer":
        result = await prd_chatbot(
            section_id,
            user_input,
            chat_history=chat_history,
            is_deep_research=1,
            BUFFER_SIZE=BUFFER_SIZE,
        )
        raw_reply = result["raw"]
        parsed_json = result["json"]
        if parsed_json:
            reply = {
                "flag": "prd_related",
                "message": parsed_json
            }
        else:
            reply = {
                "flag": "normal",
                "message": raw_reply
    }

        

        # extract prd
        # extraction = extract_prd_text(reply)
        # if extraction.get("is_prd"):
        #     prd_content = extraction.get("prd_content", "").strip()
        #     if prd_content.startswith("# Requirements Document"):
        #         save_prd(section_id, prd_content)
            # else: log lại nếu format không đúng

    elif route == "direct_answer":
        reply_string = route_info.get("content", "").strip() or "Đã nhận yêu cầu của bạn."
        reply = {
            "flag": "normal",
            "message": reply_string
        }

    else:
        # Fallback: không nhận diện được route → coi như trả lời trực tiếp
        reply_string = route_info.get("content", "Xin lỗi, tôi chưa hiểu yêu cầu của bạn.")
        reply = {
            "flag": "normal",
            "message": reply_string
        }

    # ======= LƯU MESSAGE VÀO DB =======
    # Lưu message user & bot
    save_message(db, section_id, "user", user_input)
    save_message(db, section_id, "assistant", reply["message"])

    # ======= TÓM TẮT CONTEXT (DÙNG HISTORY MỚI) =======
    # Cập nhật chat_history local để dùng cho summarize
    chat_history.append((user_input, reply))

    if len(chat_history) % CHAT_THRESHOLD == 0:
        # summarize_and_update tự lưu context vào bảng ContextItem
        summarize_and_update(
            section_id,
            chat_history=chat_history,
            CHAT_THREADHOLD=CHAT_THRESHOLD,
        )

    return reply
