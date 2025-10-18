from openai import OpenAI
from dotenv import load_dotenv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_models import Section, ContextItem, Base
from transformers import pipeline

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


def chat_with_bot(section_id, user_input):
    latest_summary = get_latest_summary(section_id)
    system_prompt = "Bạn là PM AI, hỗ trợ tạo PRD."
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
    
    print(f"Context: {messages}\n\n========================\n\n")
    chat_history.append((user_input, bot_reply))
    
    if len(chat_history) % CHAT_THREADHOLD == 0:
        summary = summarize_and_update(section_id)
        print("\n[CONTEXT UPDATED]\\n===================\n\n", summary)
        
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

def run_chat():
    section_id = create_section("fourth test")
    print(f"Created section: {section_id}\n")
    
    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Closing...")
            break
        
        reply = chat_with_bot(section_id, user_input)
        print(f"Bot: {reply}\n")
        
if __name__ == "__main__":
    print(f"Chat history: {len(chat_history)}")
    run_chat()
    
    

