from openai import OpenAI
from dotenv import load_dotenv
import os
import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.db_models import Section, ContextItem, PRD, Base
from core.mcp_client import *

from core.orchestrator import ai_orchestrator
from core.mcp_integration import mcp_integration
from core.prd_agent import prd_chatbot
from core.prd_storage import save_prd, extract_prd_text
from core.summarizer import summarize_and_update

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)



chat_history = []
CHAT_THREADHOLD = 5
BUFFER_SIZE = CHAT_THREADHOLD

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
    section_id = create_section("mcp-orchestrated-test-v22")
    print(f"Created section: {section_id}\n")

    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Closing...")
            break

        # ======= GỌI ORCHESTRATOR =======
        route_info = ai_orchestrator(user_input, section_id, chat_history, BUFFER_SIZE=BUFFER_SIZE)
        route = (route_info.get("route") or "").strip()

        if route == "call_mcp":
            print("Đang gọi MCP để lấy dữ liệu...\n")
            mcp_data = await mcp_integration(user_input)
            if mcp_data:
                enriched_input = f"{user_input}\n\n[Dữ liệu MCP thu thập được:]\n{mcp_data}"
                reply = await prd_chatbot(section_id, enriched_input, chat_history=chat_history, is_deep_research=0, BUFFER_SIZE=BUFFER_SIZE)
                
                # extract prd
                extraction = extract_prd_text(reply)
                if extraction.get("is_prd"):
                    prd_content = extraction.get("prd_content", "").strip()
                    if prd_content.startswith("# Requirements Document"):
                        save_prd(section_id, prd_content)
                        print("[PRD extracted and saved to DB]")
                    else:
                        print("[PRD format not detected correctly]")
                else:
                    print("[Không phát hiện PRD trong phản hồi.]")
            else:
                reply = "Không tìm thấy dữ liệu phù hợp từ MCP."
            # Lưu lịch sử
            chat_history.append((user_input, reply))

        elif route == "PRD_related_answer":
            reply = await prd_chatbot(section_id, user_input, chat_history=chat_history, is_deep_research= 1,  BUFFER_SIZE=BUFFER_SIZE)
            chat_history.append((user_input, reply))
            # extract prd
            extraction = extract_prd_text(reply)
            print(f"\n[PRD EXTRACTION RESULT]\n{extraction}\n")
            if extraction.get("is_prd"):
                prd_content = extraction.get("prd_content", "").strip()
                if prd_content.startswith("# Requirements Document"):
                    save_prd(section_id, prd_content)
                    print("[PRD extracted and saved to DB]")
                else:
                    print("[PRD format not detected correctly]")
            else:
                print("[Không phát hiện PRD trong phản hồi.]")

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
            summary = summarize_and_update(section_id, chat_history=chat_history, CHAT_THREADHOLD=CHAT_THREADHOLD)
            print("\n[CONTEXT UPDATED]\n", summary)

        print(f"\nBot: {reply}\n" + "-" * 90 + "\n\n")

        
if __name__ == "__main__":
    asyncio.run(run_chat())