from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from pypdf import PdfReader
import io
import os
from groq import Groq

router = APIRouter()

# إعداد عميل Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    content: str
    model: Optional[str] = "llama-3.1-8b-instant"

async def get_ai_response(prompt: str, model: str):
    try:
        from app.llm.provider import api_key
        client = Groq(api_key=api_key)
    except Exception:
        client = Groq()

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
    )
    return chat_completion.choices[0].message.content

@router.post("/messages")
async def send_message(request: ChatRequest):
    try:
        reply = await get_ai_response(request.content, request.model)
        return {
            "conversation_id": request.conversation_id or "conv_123",
            "role": "assistant",
            "content": reply
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        extracted_text = ""

        if file.filename.endswith(".pdf"):
            pdf_bytes = await file.read()
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() or ""
        elif file.filename.endswith(".txt"):
            file_bytes = await file.read()
            extracted_text = file_bytes.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم. يرجى رفع ملف PDF أو TXT.")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="الملف فارغ أو لا يحتوي على نصوص يمكن قراءتها.")

        return {
            "filename": file.filename,
            "text": extracted_text[:4000]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في قراءة الملف: {str(e)}")