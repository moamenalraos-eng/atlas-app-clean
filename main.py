from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import datetime
import os
import urllib.parse

from groq import Groq
from duckduckgo_search import DDGS

app = FastAPI(title="Atlas AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

from fastapi.staticfiles import StaticFiles

# أضف السطر ده تحت تعريف الـ app مباشرة (لو مش موجود):
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    index_file = "frontend/index.html"
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Atlas AI Assistant - Frontend not found"}
def perform_search(query: str) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(f"- {r.get('title', '')}: {r.get('body', '')}")
        return "\n".join(results) if results else "لم يتم العثور على نتائج بحث متصلة."
    except Exception as e:
        print(f"Search error: {e}")
        return "تعذر جلب نتائج البحث من الإنترنت حالياً."

def translate_prompt_to_english(prompt_arabic: str) -> str:
    """تحويل وصف الصورة العربي إلى برومبت إنجليزي فني ودقيق جداً"""
    try:
        res = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert AI image prompt generator. Convert the user's input into a high quality, detailed English image generation prompt. If the input is 'صورة خيال' or 'خيال', output 'a breathtaking surreal fantasy realm, glowing magical landscape, vibrant cosmic scenery, ultra detailed 8k artwork'. Output ONLY the English prompt string and nothing else."
                },
                {"role": "user", "content": prompt_arabic}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=120
        )
        translated = res.choices[0].message.content.strip()
        return translated if translated else prompt_arabic
    except Exception as e:
        print(f"Translation error: {e}")
        return prompt_arabic

@app.post("/api/messages")
async def handle_message(req: MessageRequest):
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_location = "القاهرة، مصر"
        user_query = req.user_input.strip()

        if not user_query:
            raise HTTPException(status_code=400, detail="الرسالة فارغة")

        # الكشف عن طلبات الرسم
        image_keywords = ["ارسم", "اعمل صوره", "اعمل صورة", "رسمة", "رسمه", "صمم صوره", "صمم صورة", "draw", "صورة"]
        user_query_lower = user_query.lower()
        
        is_image_req = any(kw in user_query_lower for kw in ["ارسم", "اعمل صوره", "اعمل صورة", "صمم صوره", "صمم صورة"])
        if is_image_req:
            prompt_text = user_query
            for kw in image_keywords:
                prompt_text = prompt_text.replace(kw, "")
            prompt_text = prompt_text.strip() or "fantasy scenery"
            
            english_prompt = translate_prompt_to_english(prompt_text)
            encoded_prompt = urllib.parse.quote(english_prompt)
            img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
            
            reply_text = f"إليك الصورة بناءً على طلبك: {prompt_text}"

            return {
                "response": reply_text,
                "image_url": img_url,
                "timestamp": current_time,
                "status": "success",
                "type": "image"
            }

        search_context = ""
        if req.internet_access:
            search_data = perform_search(user_query)
            search_context = f"\n\nمعلومات إضافية حية من الإنترنت:\n{search_data}"

        system_prompt = (
            f"أنت Atlas AI Assistant، مساعد ذكاء اصطناعي محترف.\n"
            f"تم تطويرك وبناؤك بواسطة المطور: مؤمن الجوكر (Moamen El-Joker).\n"
            f"التاريخ والوقت الحالي: {current_time}\n"
            f"الموقع الحالي للمستخدم: {current_location}\n"
            f"إذا سألك أي شخص عن من أنشأك أو طورك، أجب بفخر بأنك من تطوير مؤمن الجوكر.\n"
            f"تأكد من الرد باللغة العربية بأسلوب واضح ومباشر.{search_context}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        for item in req.history[-6:]:
            messages.append({"role": item.role, "content": item.content})
        messages.append({"role": "user", "content": user_query})

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
        )

        ai_response = chat_completion.choices[0].message.content

        return {
            "response": ai_response,
            "timestamp": current_time,
            "status": "success",
            "type": "text"
        }

    except Exception as e:
        print(f"Error handling message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-image")
async def generate_image(data: ImagePrompt):
    try:
        if not data.prompt:
            raise HTTPException(status_code=400, detail="الرجاء تقديم وصف للصورة")
        
        english_prompt = translate_prompt_to_english(data.prompt)
        encoded_prompt = urllib.parse.quote(english_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
        
        return {
            "status": "success",
            "image_url": image_url,
            "prompt": data.prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))