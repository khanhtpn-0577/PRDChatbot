# server.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from chatbot import generate_prd  # dùng hàm bạn đã có

app = FastAPI()

# Cho phép gọi từ front (http://localhost:5173, 5500, 3000,...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # cần chặt chẽ hơn thì sửa theo domain của bạn
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenReq(BaseModel):
    query: str
    context: str | None = None

@app.post("/api/generate_prd")
def api_generate_prd(req: GenReq):
    # Ghép thêm context nếu có
    full_query = req.query if not req.context else f"""{req.query}

Bổ sung context:
{req.context}
"""
    prd = generate_prd(full_query)
    return {"prd": prd}
