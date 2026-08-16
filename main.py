from fastapi import FastAPI, Response
from pydantic import BaseModel
import os
from groq import Groq
from duckduckgo_search import DDGS

# إعداد التطبيق
app = FastAPI(title="Atlas AI Assistant")

# --- تعريفات النماذج (عشان الخطأ بتاع NameError يتحل) ---
class MessageItem(BaseModel):
    role: str
    content: str

class MessageRequest(BaseModel):
    user_input: str
    stream: bool = False
    internet_access: bool = False
    history: list[MessageItem] = []

class ImagePrompt(BaseModel):
    prompt: str

# --- واجهة التطبيق (كود HTML مدمج) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Atlas AI Assistant</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding-top: 50px; }
        .card { background: #1e293b; padding: 40px; border-radius: 15px; display: inline-block; box-shadow: 0 4px 20px rgba(0,0,0,0.5); border: 1px solid #334155; }
        h1 { color: #38bdf8; margin-bottom: 20px; }
        p { font-size: 1.2rem; color: #cbd5e1; }
    </style>
</head>
<body>
    <div class="card">
        <h1>أطلس الذكي - Atlas AI</h1>
        <p>التطبيق يعمل الآن بكامل طاقته على سيرفر Railway 🚀</p>
    </div>
</body>
</html>
"""

@app.get("/")
async def serve_frontend():
    return Response(content=HTML_CONTENT, media_type="text/html")

# --- دالة البحث ---
@app.post("/search")
def perform_search(request: MessageRequest):
    try:
        query = request.user_input
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(f"{r.get('title', '')}: {r.get('body', '')}")
        return {"results": "\n".join(results) if results else "لم يتم العثور على نتائج بحث متصلة."}
    except Exception as e:
        return {"error": f"تعذر جلب نتائج البحث من الإنترنت حالياً: {str(e)}"}

# --- دالة الترجمة ---
@app.post("/translate")
def translate_prompt_to_english(prompt_data: ImagePrompt):
    # هنا تقدر تضيف كود Groq للترجمة باستخدام الـ API KEY اللي معاك
    return {"translated_prompt": "هذا الكود مخصص للترجمة"}