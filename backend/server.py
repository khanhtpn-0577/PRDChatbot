# server.py

import os
from uuid import UUID

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import logging
logger = logging.getLogger("prd-api")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.db_models import Base  # đảm bảo import để Alembic & ORM dùng chung metadata
from core.chat_service import (
    create_section,
    process_user_message,
)

# ========= CONFIG DB =========

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Tùy anh: có thể raise hoặc dùng default local
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ========= FASTAPI APP =========

app = FastAPI()

# Cho phép gọi từ frontend (http://localhost:5173, 5500, 3000,...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production nên giới hạn domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========= SCHEMA REQUEST/RESPONSE =========

class GenReq(BaseModel):
    query: str
    section_id: UUID | None = None

class ChatResponse(BaseModel):
    section_id: UUID
    response: dict


# ========= API ENDPOINT =========

@app.post("/api/generate_prd", response_model=ChatResponse)
async def api_generate_prd(req: GenReq):
    """
    - Nếu section_id = None → tạo session mới (1 Section mới).
    - Lưu message vào bảng messages.
    - Gọi orchestrator/LLM để xử lý.
    - Trả về reply + section_id để frontend giữ session.
    """
    with SessionLocal() as db:
        # 1. Tạo hoặc dùng lại section (session)
        logger.info(f"[BE] Nhận request: query={req.query}, section_id={req.section_id}")
        if req.section_id is None:
            section_id = create_section(db, name="web-session")
        else:
            section_id = req.section_id
        
        # 2. Lấy user_input
        user_input = req.query


        # 3. Gọi core service xử lý 1 lượt chat
        reply = await process_user_message(
            db=db,
            section_id=section_id,
            user_input=user_input,
        )

        return ChatResponse(
            section_id=section_id,
            response=reply,
        )

