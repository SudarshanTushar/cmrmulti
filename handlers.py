import logging
import base64
import io
import asyncio
import re
import os
import httpx
import speech_recognition as sr
from pydub import AudioSegment
from openai import AsyncOpenAI
from gtts import gTTS
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from duckduckgo_search import DDGS
from pypdf import PdfReader  # PDF handling

from config import SAMBANOVA_API_KEY, SAMBANOVA_BASE_URL
from db import get_history, add_history, clear_history

# --- AI CONFIGURATION ---
# Hum same client use karenge Text aur Images dono ke liye
aclient = AsyncOpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url=SAMBANOVA_BASE_URL
)

# --- MODEL LIST ---
# Text ke liye Llama 3.3, Images ke liye Llama 3.2 Vision
TEXT_MODEL = "Meta-Llama-3.3-70B-Instruct"
VISION_MODEL = "Llama-3.2-11B-Vision-Instruct" 

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are 'Pathsetu', an Elite AI Assistant & Career Guardian.

### YOUR CAPABILITIES:
1. **CODING EXPERT:** You can analyze, debug, and generate code in Python, Java, C++, JavaScript, etc. Always explain the logic.
2. **DOCUMENT ANALYST:** You can read PDF contexts provided to you and answer questions based on them.
3. **IMAGE ANALYST:** You can see images and explain them.
4. **CAREER GUIDE:** Bridge the gap between rural students and modern opportunities.

### CORE RULES:
- **DETECT LANGUAGE:** Reply in the EXACT language of the user (Hindi/Marathi/English etc).
- **VISUALS:** Use `mermaid` graphs for roadmaps (Current -> Action -> Goal).
- **ACCURACY:** Be precise. No fluff.
- **FORMAT:** Use Markdown. For code, use code blocks.
"""

# --- HELPER FUNCTIONS ---

async def perform_web_search(query):
    try:
        results = await asyncio.to_thread(lambda: list(DDGS().text(query, max_results=3)))
        if not results: return None
        summary = "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in results])
        return f"\n\n[WEB_SEARCH_RESULTS]:\n{summary}\n"
    except Exception as e:
        logging.error(f"Search Error: {e}")
        return None

async def extract_pdf_text(client, message):
    try:
        doc_path = await client.download_media(message)
        reader = PdfReader(doc_path)
        text = ""
        # Limit to first 10 pages
        for page in reader.pages[:10]: 
            text += page.extract_text() + "\n"
        os.remove(doc_path)
        return text[:12000] # Token limit safety
    except Exception as e:
        logging.error(f"PDF Error: {e}")
        return None

async def transcribe_audio(file_bytes):
    try:
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format="ogg")
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            text = recognizer.recognize_google(recognizer.record(source))
            return text
    except Exception as e:
        logging.error(f"Transcribe Error: {e}")
        return None

def text_to_audio(text):
    try:
        clean_text = re.sub(r"```mermaid.*?```", "", text, flags=re.DOTALL)
        clean_text = clean_text.replace("*", "").replace("#", "").replace("- ", " ")
        lang_code = 'en'
        if any('\u0900' <= char <= '\u097f' for char in text): # Devanagari check
            lang_code = 'hi'
        
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        audio_io.name = "guidance.mp3"
        return audio_io
    except Exception as e:
        logging.error(f"TTS Error: {e}")
        return None

async def get_mermaid_image(mermaid_code):
    try:
        graph_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
        if "%%{init:" not in graph_code:
            graph_code = "%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffcc00', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#fff'}}}%%\n" + graph_code
        graph_code = graph_code.replace("graph LR", "graph TD")
        b64 = base64.urlsafe_b64encode(graph_code.encode("utf8")).decode('ascii')
        url = f"https://mermaid.ink/img/{b64}?bgColor=FFFFFF"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=20.0)
            if resp.status_code == 200:
                file_obj = io.BytesIO(resp.content)
                file_obj.name = "career_path.jpg"
                return file_obj, url
            return None, None
    except Exception as e:
        logging.error(f"Mermaid Error: {e}")
        return None, None

# --- CORE GENERATION LOGIC ---

async def analyze_image_samba(client, message, prompt):
    """SambaNova Vision Model Handler"""
    try:
        # Download photo
        photo_path = await client.download_media(message)
        
        # Convert to Base64
        with open(photo_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        os.remove(photo_path) # Cleanup

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        response = await aclient.chat.completions.create(
            model=VISION_MODEL,
            messages=messages,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Vision Error: {e}")
        return "⚠️ Image analysis failed. Server might be busy."

async def generate_text_response(history, user_prompt, context_data=""):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        for entry in history[-4:]:
            role = "assistant" if entry.get("role") == "model" else "user"
            content = entry.get("parts", [""])[0]
            messages.append({"role": role, "content": str(content)})
            
    final_content = user_prompt
    if context_data:
        final_content = f"CONTEXT DATA (PDF/FILE/SEARCH):\n{context_data}\n\nUSER QUESTION: {user_prompt}"

    messages.append({"role": "user", "content": final_content})

    try:
        resp = await aclient.chat.completions.create(
            model=TEXT_MODEL, messages=messages, temperature=0.6, max_tokens=1500
        )
        return resp.choices[0].message.content
    except Exception as e:
        logging.error(f"Text Model Error: {e}")
        return "⚠️ Server Busy. Try again."

# --- MAIN HANDLERS ---

async def start_handler(client: Client, message: Message):
    await clear_history(message.chat.id)
    await message.reply(
        "**🚀 Pathsetu AI Ultimate**\n\n"
        "Fully upgraded with Vision & Documents:\n"
        "📄 **PDF Reader:** Send any PDF.\n"
        "🖼️ **Vision Eye:** Send any Photo.\n"
        "💻 **Code:** I can code in any language.\n\n"
        "Try sending a file now!"
    )

async def chat_handler(client: Client, message: Message):
    chat_id = message.chat.id
    context_data = ""
    user_prompt = ""
    display_text = ""
    
    try:
        await client.send_chat_action(chat_id, enums.ChatAction.TYPING)

        # 1. HANDLE IMAGES (Priority)
        if message.photo:
            await client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_PHOTO)
            caption = message.caption or "Describe this image in detail."
            ai_text = await analyze_image_samba(client, message, caption)
            
            await message.reply(f"**🖼️ Vision Analysis:**\n\n{ai_text}", parse_mode=enums.ParseMode.MARKDOWN)
            await add_history(chat_id, f"[Image Sent]: {caption}", ai_text)
            return

        # 2. HANDLE VOICE
        if message.voice:
            voice_bytes = bytes((await message.download(in_memory=True)).getbuffer())
            transcription = await transcribe_audio(voice_bytes)
            if not transcription:
                await message.reply("⚠️ Could not hear audio.")
                return
            user_prompt = transcription
            display_text = f"🎤 {user_prompt}"

        # 3. HANDLE TEXT
        elif message.text:
            user_prompt = message.text
            display_text = message.text

        # 4. HANDLE DOCUMENTS (PDF/Code)
        elif message.document:
            if message.document.mime_type == "application/pdf":
                await message.reply("📄 Reading PDF...", quote=True)
                pdf_text = await extract_pdf_text(client, message)
                if pdf_text:
                    context_data += f"\n[PDF CONTENT]:\n{pdf_text}\n"
                    user_prompt = message.caption or "Summarize this document."
                    display_text = f"📄 Uploaded PDF: {message.document.file_name}"
                else:
                    await message.reply("❌ Could not read PDF text.")
                    return
            else:
                # Code files or txt
                try:
                    file_content = await client.download_media(message, in_memory=True)
                    text_content = file_content.getvalue().decode('utf-8')
                    context_data += f"\n[FILE CONTENT]:\n{text_content}\n"
                    user_prompt = message.caption or "Analyze this file."
                    display_text = f"📁 Uploaded File: {message.document.file_name}"
                except:
                    await message.reply("❌ Only PDF or Text-based files supported.")
                    return

        # 5. SEARCH & GENERATE
        triggers = ["salary", "job", "opening", "vacancy", "news", "trend"]
        if user_prompt and any(x in user_prompt.lower() for x in triggers):
            search_res = await perform_web_search(user_prompt + " India")
            if search_res: context_data += search_res

        past_history = await get_history(chat_id)
        ai_text = await generate_text_response(past_history, user_prompt, context_data)
        await add_history(chat_id, display_text, ai_text)

        # 6. MERMAID GRAPHICS
        if "```mermaid" in ai_text:
            matches = re.findall(r"```mermaid(.*?)```", ai_text, re.DOTALL)
            if matches:
                image_file, _ = await get_mermaid_image(matches[0].strip())
                ai_text = re.sub(r"```mermaid(.*?)```", "", ai_text, flags=re.DOTALL).strip()
                if image_file:
                    await client.send_photo(chat_id, photo=image_file)

        # 7. FINAL REPLY
        if message.voice:
            audio = text_to_audio(ai_text)
            if audio: 
                await message.reply_voice(audio, caption=ai_text[:200])
            else: 
                await message.reply(ai_text, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await message.reply(ai_text, parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        logging.error(f"Handler Error: {e}")
        await message.reply(f"⚠️ Error: {str(e)}")

def register_handlers(app: Client):
    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    app.add_handler(MessageHandler(chat_handler, (filters.text | filters.voice | filters.document | filters.photo) & ~filters.command("start")))
