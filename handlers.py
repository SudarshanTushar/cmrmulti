import logging
import base64
import io
import asyncio
import re
import httpx
import speech_recognition as sr
from pydub import AudioSegment
from openai import AsyncOpenAI
from gtts import gTTS
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InputMediaPhoto
from pyrogram.handlers import MessageHandler
from duckduckgo_search import DDGS
from config import SAMBANOVA_API_KEY, SAMBANOVA_BASE_URL
from db import get_history, add_history, clear_history

# --- AI CONFIGURATION ---
aclient = AsyncOpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url=SAMBANOVA_BASE_URL
)

# --- MODEL LIST ---
MODEL_LIST = [
    "Meta-Llama-3.3-70B-Instruct",
    "Meta-Llama-3.1-70B-Instruct", 
    "Meta-Llama-3.1-8B-Instruct",
]

# --- 🧠 UNIFIED SYSTEM INTELLIGENCE ---
SYSTEM_PROMPT = """
You are 'Pathsetu', an AI Career Guardian for students.
Your mission: Bridge the gap between rural students and modern career opportunities.

### CORE OPERATING RULES:
1. **MULTILINGUAL ADAPTATION:** - DETECT the language of the user's prompt. 
   - REPLY IN THE EXACT SAME LANGUAGE.
   - If the user speaks Hindi, you speak Hindi. If Marathi, you speak Marathi.

2. **LOCALIZED INTELLIGENCE:**
   - Prioritize jobs accessible in India (remote or local).
   - Suggest low-cost, high-value skills (e.g., YouTube learning, free certifications).

3. **VISUAL ROADMAPS:**
   - If the user asks "How to become X?" or "Roadmap", you MUST generate a `mermaid` graph.
   - Use `graph TD` layout.
   - Structure: [Current Skill] --> [Action] --> [New Skill] --> [Job].

4. **VOICE-FIRST BREVITY:**
   - Keep answers concise (under 100 words).
   - Use bullet points.
   - No complex URLs or code blocks unless requested.

### CONTEXTUAL DATA:
Use [WEB_SEARCH_RESULTS] for real-time salary and job market trends.
"""

# --- SEARCH ENGINE ---
def search_sync(query):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=3))
    except Exception as e:
        logging.error(f"Search Error: {e}")
        return None

async def perform_web_search(query):
    try:
        results = await asyncio.to_thread(search_sync, query)
        if not results: return None
        summary = "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in results])
        return f"\n\n[WEB_SEARCH_RESULTS]:\n{summary}\n"
    except Exception as e:
        logging.error(f"Async Search Error: {e}")
        return None

# --- AUDIO & GRAPHICS ---
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

async def get_mermaid_image(mermaid_code):
    try:
        # Cleanup code
        graph_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
        
        # Style injection
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

def text_to_audio(text):
    try:
        # Clean text for speech
        clean_text = re.sub(r"```mermaid.*?```", "", text, flags=re.DOTALL)
        clean_text = clean_text.replace("*", "").replace("#", "").replace("- ", " ")
        
        # Detect language
        lang_code = 'en'
        if any('\u0900' <= char <= '\u097f' for char in text): # Devanagari
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

# --- GENERATION LOGIC ---
async def generate_response(history, user_prompt, search_context=""):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        for entry in history[-4:]:
            role = "assistant" if entry.get("role") == "model" else "user"
            content = entry.get("parts", [""])[0] if isinstance(entry.get("parts"), list) else str(entry.get("parts", ""))
            messages.append({"role": role, "content": content})
            
    final_content = user_prompt
    if search_context:
        final_content = f"LATEST MARKET DATA:\n{search_context}\n\nUSER QUESTION: {user_prompt}"

    messages.append({"role": "user", "content": final_content})

    for model in MODEL_LIST:
        try:
            resp = await aclient.chat.completions.create(
                model=model, messages=messages, temperature=0.6, max_tokens=1000
            )
            return resp.choices[0].message.content
        except Exception as e:
            logging.error(f"Model Error ({model}): {e}")
            continue
    return "⚠️ Server Busy. Try again."

# --- HANDLERS ---
async def start_handler(client: Client, message: Message):
    await clear_history(message.chat.id)
    await message.reply(
        "** नमस्ते! Welcome to Pathsetu.** 🇮🇳\n\n"
        "I am your AI Career Guide. \n"
        "**You can speak to me in your language.**\n\n"
        "🎤 **Send a Voice Note** or 📝 **Type a Message**.\n"
        "Try: *'How to become a Web Developer?'*"
    )

async def chat_handler(client: Client, message: Message):
    chat_id = message.chat.id
    
    try:
        # 1. Input Processing
        if message.voice:
            await client.send_chat_action(chat_id, enums.ChatAction.RECORD_AUDIO)
            voice_bytes = bytes((await message.download(in_memory=True)).getbuffer())
            user_prompt = await transcribe_audio(voice_bytes)
            if not user_prompt:
                await message.reply("⚠️ Could not hear audio.")
                return
            display_text = f"🎤 {user_prompt}"
        else:
            await client.send_chat_action(chat_id, enums.ChatAction.TYPING)
            user_prompt = message.text
            display_text = message.text

        # 2. Search Trigger
        search_context = ""
        triggers = ["salary", "jobs", "openings", "vacancy", "future", "scope", "demand", "price"]
        if any(x in user_prompt.lower() for x in triggers):
            await client.send_chat_action(chat_id, enums.ChatAction.FIND_LOCATION)
            search_context = await perform_web_search(user_prompt + " India jobs")

        # 3. Generate
        past_history = await get_history(chat_id)
        ai_text = await generate_response(past_history, user_prompt, search_context)
        await add_history(chat_id, display_text, ai_text)

        # 4. Graphics
        if "```mermaid" in ai_text:
            try:
                matches = re.findall(r"```mermaid(.*?)```", ai_text, re.DOTALL)
                if matches:
                    image_file, _ = await get_mermaid_image(matches[0].strip())
                    ai_text = re.sub(r"```mermaid(.*?)```", "", ai_text, flags=re.DOTALL).strip()
                    if image_file:
                        await client.send_photo(chat_id, photo=image_file, caption="**📊 Career Roadmap**")
            except Exception as e:
                logging.error(f"Graph Error: {e}")

        # 5. Reply
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
        await message.reply(f"⚠️ Error: {e}")

def register_handlers(app: Client):
    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    app.add_handler(MessageHandler(chat_handler, (filters.text | filters.voice) & ~filters.command("start")))
