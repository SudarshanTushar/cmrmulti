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

# --- AI CLIENT CONFIGURATION ---
aclient = AsyncOpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url=SAMBANOVA_BASE_URL
)

# --- MODELS ---
# Text Model: Powerful logic & coding (Llama 3.3 70B)
TEXT_MODEL = "Meta-Llama-3.3-70B-Instruct"
# Vision Model: For viewing images (Llama 3.2 11B Vision)
VISION_MODEL = "Llama-3.2-11B-Vision-Instruct" 

# --- SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are 'Pathsetu', an Elite AI Assistant.

### CORE INSTRUCTIONS:
1. **LANGUAGE ADAPTATION:** - DETECT the user's language (English, Hindi, Marathi, Telugu, etc.).
   - **REPLY IN THE EXACT SAME LANGUAGE.**
   - If the user mixes languages (Hinglish), reply in Hinglish.

2. **CAPABILITIES:**
   - **Coding Expert:** Write, debug, and explain code in Python, Java, C++, JS, etc.
   - **Document Analyst:** Summarize and answer questions from provided PDF context.
   - **Image Analyst:** Explain images provided in the context.
   - **Career Guide:** Provide roadmaps and guidance.

3. **FORMATTING:**
   - Use Markdown (**Bold**, `Code Blocks`, *Italic*).
   - For roadmaps, use `mermaid` graph TD.
   - Be concise and direct.
"""

# --- HELPER FUNCTIONS ---

async def perform_web_search(query):
    """Searches the web for real-time info (Salary, Jobs, etc.)"""
    try:
        results = await asyncio.to_thread(lambda: list(DDGS().text(query, max_results=3)))
        if not results: return None
        summary = "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in results])
        return f"\n\n[WEB_SEARCH_RESULTS]:\n{summary}\n"
    except Exception as e:
        logging.error(f"Search Error: {e}")
        return None

async def extract_pdf_text(client, message):
    """Extracts text from PDF. Returns None if scanned/empty."""
    try:
        doc_path = await client.download_media(message)
        reader = PdfReader(doc_path)
        text = ""
        # Limit to first 15 pages to save speed/tokens
        for page in reader.pages[:15]: 
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        os.remove(doc_path) # Cleanup file
        
        # CHECK: If text is too short, it's likely a Scanned PDF (Images)
        if len(text.strip()) < 50:
            return None 
            
        return text[:15000] # Limit characters
    except Exception as e:
        logging.error(f"PDF Error: {e}")
        return None

async def analyze_image_samba(client, message, prompt):
    """Uses SambaNova Vision model to see images."""
    try:
        photo_path = await client.download_media(message)
        
        # Convert image to Base64 for the API
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
        logging.error(f"Vision Error: {e}")
        return "⚠️ Error: I could not analyze the image. Server might be busy."

async def transcribe_audio(file_bytes):
    """Converts Voice Note to Text."""
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
    """Converts Text Reply to Voice Note."""
    try:
        # Remove code blocks for speech
        clean_text = re.sub(r"```.*?```", "Code snippet provided.", text, flags=re.DOTALL)
        clean_text = clean_text.replace("*", "").replace("#", "")
        
        # Simple Language Detection for TTS
        lang_code = 'en'
        if any('\u0900' <= char <= '\u097f' for char in text): # Devanagari range
            lang_code = 'hi'
            
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        audio_io.name = "response.mp3"
        return audio_io
    except:
        return None

async def generate_text_response(history, user_prompt, context_data=""):
    """Core Logic: Sends prompt + context to SambaNova Llama 3.3"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add Chat History
    if history:
        for entry in history[-4:]:
            role = "assistant" if entry.get("role") == "model" else "user"
            content = entry.get("parts", [""])[0]
            messages.append({"role": role, "content": str(content)})
            
    # Combine Context + Prompt
    final_content = user_prompt
    if context_data:
        final_content = f"### CONTEXT DATA (File/Search):\n{context_data}\n\n### USER QUESTION:\n{user_prompt}"

    messages.append({"role": "user", "content": final_content})

    try:
        resp = await aclient.chat.completions.create(
            model=TEXT_MODEL, messages=messages, temperature=0.6, max_tokens=1500
        )
        return resp.choices[0].message.content
    except Exception as e:
        logging.error(f"Text Model Error: {e}")
        return "⚠️ AI Server is busy. Please try again in 5 seconds."

# --- MAIN HANDLERS ---

async def start_handler(client: Client, message: Message):
    await clear_history(message.chat.id)
    await message.reply(
        "**🤖 Pathsetu AI Online**\n\n"
        "I am ready. I can help you with:\n"
        "📄 **PDFs:** Send file to read.\n"
        "🖼️ **Images:** Send photo to analyze.\n"
        "💻 **Coding:** Ask any programming question.\n"
        "🗣️ **Voice:** I speak your language.\n\n"
        "*Send a message to start!*"
    )

async def chat_handler(client: Client, message: Message):
    chat_id = message.chat.id
    context_data = ""
    user_prompt = ""
    display_text = ""
    
    try:
        await client.send_chat_action(chat_id, enums.ChatAction.TYPING)

        # 1. HANDLE PHOTOS (Vision)
        if message.photo:
            await client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_PHOTO)
            caption = message.caption or "Explain this image."
            ai_text = await analyze_image_samba(client, message, caption)
            
            await message.reply(f"**🖼️ Image Analysis:**\n\n{ai_text}", parse_mode=enums.ParseMode.MARKDOWN)
            await add_history(chat_id, f"[Image]: {caption}", ai_text)
            return

        # 2. HANDLE DOCUMENTS (PDF / Code)
        elif message.document:
            if message.document.mime_type == "application/pdf":
                status_msg = await message.reply("📄 Reading PDF...", quote=True)
                pdf_text = await extract_pdf_text(client, message)
                
                if pdf_text:
                    context_data += f"\n[PDF CONTENT]:\n{pdf_text}\n"
                    user_prompt = message.caption or "Summarize this PDF."
                    display_text = f"📄 PDF: {message.document.file_name}"
                    await status_msg.delete()
                else:
                    # SCANNED PDF DETECTED
                    await status_msg.edit(
                        "⚠️ **Cannot Read Text**\n\n"
                        "This looks like a **Scanned PDF** (Images inside PDF).\n"
                        "👉 **Solution:** Take a Screenshot of the page and send it as a **Photo**."
                    )
                    return
            else:
                # Text/Code Files (.py, .txt, etc.)
                try:
                    file_content = await client.download_media(message, in_memory=True)
                    text_content = file_content.getvalue().decode('utf-8')
                    context_data += f"\n[FILE CONTENT]:\n{text_content}\n"
                    user_prompt = message.caption or "Analyze this code/file."
                    display_text = f"📁 File: {message.document.file_name}"
                except:
                    await message.reply("❌ Supported formats: PDF, Text, Code files, Photos.")
                    return

        # 3. HANDLE VOICE
        elif message.voice:
            voice_bytes = bytes((await message.download(in_memory=True)).getbuffer())
            transcription = await transcribe_audio(voice_bytes)
            if not transcription:
                await message.reply("⚠️ Audio not clear.")
                return
            user_prompt = transcription
            display_text = f"🎤 {user_prompt}"

        # 4. HANDLE TEXT
        elif message.text:
            user_prompt = message.text
            display_text = message.text

        # 5. SEARCH & GENERATE
        triggers = ["salary", "job", "vacancy", "news", "price", "stock"]
        if user_prompt and any(x in user_prompt.lower() for x in triggers):
            search_res = await perform_web_search(user_prompt + " India")
            if search_res: context_data += search_res

        if not user_prompt: user_prompt = "Explain the uploaded content."

        # Get Response
        past_history = await get_history(chat_id)
        ai_text = await generate_text_response(past_history, user_prompt, context_data)
        await add_history(chat_id, display_text, ai_text)

        # 6. REPLY (Text or Voice)
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
