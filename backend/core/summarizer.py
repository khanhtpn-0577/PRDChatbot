import os
from openai import OpenAI
from dotenv import load_dotenv
from db.db_models import ContextItem
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine



load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

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
def summarize_and_update(section_id, chat_history, CHAT_THREADHOLD=5):
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
