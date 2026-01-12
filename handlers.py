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
from pypdf import PdfReader

from config import SAMBANOVA_API_KEY, SAMBANOVA_BASE_URL
from db import get_history, add_history, clear_history

# --- AI CLIENT ---
aclient = AsyncOpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url=SAMBANOVA_BASE_URL
)

TEXT_MODEL = "Meta-Llama-3.3-70B-Instruct"
VISION_MODEL = "Llama-3.2-11B-Vision-Instruct" 

# --- UPDATED SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are 'Pathsetu', an Elite AI Assistant.

### CRITICAL RULES:
1. **CONTEXT AWARENESS:** The system has ALREADY read the file and provided the text in the message below marked as `[FILE_CONTENT_START]`. 
   - **DO NOT** say "I cannot read files". 
   - **DO NOT** say "I am an AI model and cannot access external files".
   - Treat the text provided in `[FILE_CONTENT]` as if you read the file yourself.

2. **MEMORY:** You must remember the content of the file for follow-up questions.

3. **LANGUAGE:** Reply in the EXACT language of the user.

4. **FORMAT:** Use Markdown. Use `mermaid` graph TD for processes.
"""

# --- HELPERS ---

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
        # Read up to 15 pages
        for page in reader.pages[:15]: 
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        os.remove(doc_path)
        
        # Scanned PDF Check
        if len(text.strip()) < 50:
            return None 
            
        return text[:15000] # Limit to 15k chars for memory safety
    except Exception as e:
        logging.error(f"PDF Error: {e}")
        return None

async def analyze_image_samba(client, message, prompt):
    try:
        photo_path = await client.download_media(message)
        with open(photo_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        os.remove(photo_path)

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
        response = await aclient.chat.completions.create(
            model=VISION_MODEL, messages=messages, max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return "⚠️ I could not see the image. Server busy."

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
    except:
        return None

def text_to_audio(text):
    try:
        clean_text = re.sub(r"```.*?```", "Code snippet.", text, flags=re.DOTALL)
        clean_text = clean_text.replace("*", "").replace("#", "")
        lang_code = 'en'
        if any('\u0900' <= char <= '\u097f' for char in text): 
            lang_code = 'hi'
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        audio_io.name = "response.mp3"
        return audio_io
    except:
        return None

# --- GENERATION LOGIC ---

async def generate_text_response(history, user_prompt, current_file_content=""):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 1. Add Chat History (This now includes previous PDF text from DB)
    if history:
        for entry in history[-4:]: # Last 4 turns
            role = "assistant" if entry.get("role") == "model" else "user"
            content = entry.get("parts", [""])[0]
            messages.append({"role": role, "content": str(content)})
            
    # 2. Add CURRENT New File Content (if any)
    final_user_message = user_prompt
    if current_file_content:
        final_user_message = f"""
        MY QUESTION: {user_prompt}
        
        [SYSTEM: THE FILE HAS BEEN OPENED. HERE IS THE CONTENT:]
        [FILE_CONTENT_START]
        {current_file_content}
        [FILE_CONTENT_END]
        """

    messages.append({"role": "user", "content": final_user_message})

    try:
        resp = await aclient.chat.completions.create(
            model=TEXT_MODEL, messages=messages, temperature=0.6, max_tokens=1500
        )
        return resp.choices[0].message.content
    except Exception as e:
        logging.error(f"Model Error: {e}")
        return "⚠️ Server busy."

# --- HANDLERS ---

async def start_handler(client: Client, message: Message):
    await clear_history(message.chat.id)
    await message.reply("**Pathsetu AI Ready.** Send a PDF, Image, or Audio.")

async def chat_handler(client: Client, message: Message):
    chat_id = message.chat.id
    current_file_content = "" # Only for THIS turn
    user_prompt = ""
    display_text = "" # What is saved to DB
    
    try:
        await client.send_chat_action(chat_id, enums.ChatAction.TYPING)

        # 1. IMAGE (Vision)
        if message.photo:
            ai_text = await analyze_image_samba(client, message, message.caption or "Explain image")
            await message.reply(f"**🖼️ Analysis:**\n{ai_text}", parse_mode=enums.ParseMode.MARKDOWN)
            await add_history(chat_id, f"[Image Sent]: {message.caption}", ai_text)
            return

        # 2. PDF / DOCUMENT
        elif message.document:
            if message.document.mime_type == "application/pdf":
                status_msg = await message.reply("📄 Processing PDF...", quote=True)
                pdf_text = await extract_pdf_text(client, message)
                
                if pdf_text:
                    # IMPORTANT: We attach text to this variable
                    current_file_content = pdf_text
                    user_prompt = message.caption or "Analyze this PDF file."
                    
                    # MEMORY FIX: We save the full text to DB so it remembers later
                    display_text = f"{user_prompt}\n\n[UPLOADED PDF CONTENT]:\n{pdf_text}"
                    await status_msg.delete()
                else:
                    await status_msg.edit("⚠️ **Scanned PDF Detected.** Please send a Screenshot (Photo) instead.")
                    return
            else:
                # Text/Code Files
                file_content = await client.download_media(message, in_memory=True)
                text_content = file_content.getvalue().decode('utf-8')
                current_file_content = text_content
                user_prompt = message.caption or "Analyze code."
                display_text = f"{user_prompt}\n\n[FILE CONTENT]:\n{text_content}"

        # 3. VOICE
        elif message.voice:
            voice_bytes = bytes((await message.download(in_memory=True)).getbuffer())
            user_prompt = await transcribe_audio(voice_bytes)
            if not user_prompt: 
                await message.reply("⚠️ Audio unclear.")
                return
            display_text = f"🎤 {user_prompt}"

        # 4. TEXT
        elif message.text:
            user_prompt = message.text
            display_text = message.text

        # 5. SEARCH (Only if no file attached)
        if not current_file_content and any(x in str(user_prompt).lower() for x in ["salary", "job", "news"]):
            search_res = await perform_web_search(user_prompt + " India")
            if search_res: 
                user_prompt += f"\n{search_res}"
                display_text += f"\n{search_res}"

        # 6. GENERATE & SAVE
        past_history = await get_history(chat_id)
        
        # If we have file content, we pass it. If not, we pass empty (but history has previous files)
        ai_text = await generate_text_response(past_history, user_prompt, current_file_content)
        
        # CRITICAL: Save the display_text (which contains PDF content) to DB
        await add_history(chat_id, display_text, ai_text)

        # 7. REPLY
        if message.voice:
            audio = text_to_audio(ai_text)
            if audio: await message.reply_voice(audio)
            else: await message.reply(ai_text, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await message.reply(ai_text, parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.reply(f"⚠️ Error: {str(e)}")

def register_handlers(app: Client):
    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    app.add_handler(MessageHandler(chat_handler, (filters.text | filters.voice | filters.document | filters.photo) & ~filters.command("start")))
