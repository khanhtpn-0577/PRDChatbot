import json, re, os
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.db_models import Section, ContextItem, PRD, Base

load_dotenv()
client = OpenAI()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def save_prd(section_id, prd_text):
    """
    Lưu PRD mới nhất vào bảng PRD, tự tăng version và vô hiệu hóa các bản active cũ.
    Đảm bảo chỉ có 1 bản is_active=True tại mọi thời điểm.
    """
    with SessionLocal() as db:
        #Lấy tất cả bản đang active
        active_items = (
            db.query(PRD)
            .filter(PRD.section_id == section_id, PRD.is_active == True)
            .all()
        )

        # Nếu có active bản cũ → tắt tất cả
        for item in active_items:
            item.is_active = False

        # Tìm version cao nhất hiện tại để tăng thêm 1
        latest = (
            db.query(PRD)
            .filter(PRD.section_id == section_id)
            .order_by(PRD.version.desc())
            .first()
        )
        new_version = 1 if latest is None else latest.version + 1

        # Tạo bản mới active duy nhất
        new_prd = PRD(
            section_id=section_id,
            prd_text=prd_text.strip(),
            version=new_version,
            is_active=True,
        )
        db.add(new_prd)
        db.commit()
        print(f"[SAVED PRD v{new_version}] Section {section_id}")

def extract_prd_text(full_text):
    """
    Dùng AI kiểm tra xem phản hồi có chứa PRD không.
    Nếu có, tách riêng phần PRD theo định dạng Markdown chuẩn.
    """
    system_prompt = """
Bạn là một AI Extractor. 
Đầu vào là một đoạn văn bản có thể chứa PRD hoặc lời giới thiệu khác.
Nhiệm vụ của bạn:
1. Nếu KHÔNG có PRD trong văn bản, trả về JSON: {"is_prd": false}.
2. Nếu CÓ PRD (bắt đầu bằng '# Requirements Document'), 
   hãy trích xuất NGUYÊN PHẦN PRD và trả về JSON:
   {
      "is_prd": true,
      "prd_content": "<nội dung đầy đủ từ # Requirements Document trở đi>"
   }

Chỉ trả về JSON hợp lệ, không thêm lời giải thích.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_text},
        ],
        temperature=0,
        max_tokens=800,
    )
    text = response.choices[0].message.content.strip()
    print(f"\n[PRD EXTRACTION RAW OUTPUT]\n{text}\n")
    
    match = re.search(r"\{.*?\}", text, re.DOTALL)

    if not match:
        return {"notice": "No JSON found", "is_prd": False}

    try:
        data = json.loads(match.group(0))
        print(f"\n[Parsed PRD Extraction Data]\n{data}\n")
        return data
    except Exception:
        return {"notice": "JSON parse error", "is_prd": False}