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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from duckduckgo_search import DDGS
from config import SAMBANOVA_API_KEY, SAMBANOVA_BASE_URL
from db import get_history, add_history, clear_history, set_user_mode, get_user_mode

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

# --- 🎭 PERSONA PROMPTS ---
BASE_INSTRUCTIONS = """
CORE DIRECTIVES:
1. **LANGUAGE:** ALWAYS reply in the SAME language the user speaks.
2. **GRAPHICS:** If asked for a Roadmap, generate a `mermaid` code block (graph TD).
3. **REAL-TIME:** Use [WEB_SEARCH_RESULTS] if provided.
"""

PERSONAS = {
    "father": """You are the user's **FATHER**. 
    **Tone:** Strict but loving, protective, authoritative, and practical. 
    **Focus:** Financial security, responsibility, future stability, and discipline.
    **Style:** Use phrases like "Listen to me son/daughter", "Work hard", "Don't waste time". Give fatherly advice.""",
    
    "mother": """You are the user's **MOTHER**. 
    **Tone:** Extremely caring, emotional, warm, and worried about well-being.
    **Focus:** Health, happiness, safety, and emotional support.
    **Style:** Use phrases like "Mera bachha", "Are you eating well?", "Don't stress too much". Be very nurturing.""",
    
    "brother": """You are the user's **ELDER BROTHER**. 
    **Tone:** Practical, 'tough love', casual, and protective.
    **Focus:** Career growth, hustle, reality checks, and taking action.
    **Style:** Use slang suitable for brothers, "Bro", "Listen", "Don't be stupid". Push them to be strong.""",
    
    "sister": """You are the user's **SISTER**. 
    **Tone:** Friendly, slightly teasing, supportive, and a confidante.
    **Focus:** Emotional balance, social trends, modern advice, and empathy.
    **Style:** Casual, chatty, use emojis. Be like a best friend who gives advice.""",
    
    "teacher": """You are the user's **TEACHER (Guru)**. 
    **Tone:** Formal, wise, encouraging, and disciplined.
    **Focus:** Knowledge, syllabus, learning paths, accuracy, and academic success.
    **Style:** Respectful, informative, guiding. Call the user 'Student' or by name."""
}

# --- SEARCH ENGINE ---
def search_sync(query):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=3))
    except:
        return None

async def perform_web_search(query):
    try:
        results = await asyncio.to_thread(search_sync, query)
        if not results: return None
        summary = "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in results])
        return f"\n\n[WEB_SEARCH_RESULTS]:\n{summary}\n"
    except:
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
    except:
        return None

async def get_mermaid_image(mermaid_code):
    try:
        graph_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
        if "%%{init:" not in graph_code:
            graph_code = "%%{init: {'theme': 'neutral', 'scale': 3}}%%\n" + graph_code
        graph_code = graph_code.replace("graph LR", "graph TD")
        b64 = base64.urlsafe_b64encode(graph_code.encode("utf8")).decode('ascii')
        url = f"https://mermaid.ink/img/{b64}?bgColor=FFFFFF"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=20.0)
            if resp.status_code == 200:
                file_obj = io.BytesIO(resp.content)
                file_obj.name = "roadmap.jpg"
                return file_obj, url
            return None, None
    except:
        return None, None

def text_to_audio(text):
    try:
        lang_code = 'en'
        if any('\u0900' <= char <= '\u097f' for char in text): lang_code = 'hi'
        tts = gTTS(text=text, lang=lang_code, slow=False)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        audio_io.name = "reply.mp3"
        return audio_io
    except:
        return None

# --- GENERATION LOGIC ---
async def generate_with_fallback(history, user_prompt, user_mode="teacher", search_context=""):
    # 1. Select the correct System Prompt based on Mode
    persona_prompt = PERSONAS.get(user_mode, PERSONAS["teacher"])
    full_system_prompt = f"{persona_prompt}\n{BASE_INSTRUCTIONS}"
    
    messages = [{"role": "system", "content": full_system_prompt}]
    
    if history:
        for entry in history:
            role = "assistant" if entry.get("role") == "model" else "user"
            content = entry.get("parts", [""])[0] if isinstance(entry.get("parts"), list) else str(entry.get("parts", ""))
            messages.append({"role": role, "content": content})
            
    final_content = user_prompt
    if search_context:
        final_content = f"Context:\n{search_context}\n\nUser: {user_prompt}"

    messages.append({"role": "user", "content": final_content})

    for model in MODEL_LIST:
        try:
            resp = await aclient.chat.completions.create(
                model=model, messages=messages, temperature=0.7, max_tokens=1000
            )
            return resp.choices[0].message.content
        except:
            continue
    return "⚠️ I am having trouble thinking right now."

# --- HANDLERS ---
async def start_handler(client: Client, message: Message):
    await clear_history(message.chat.id)
    await message.reply(
        "**Namaste! 🙏**\n\nI can talk to you in 5 different modes:\n"
        "👨‍👧 **Father** (Strict & Protective)\n"
        "🤱 **Mother** (Caring & Emotional)\n"
        "🤛 **Brother** (Tough Love)\n"
        "💁‍♀️ **Sister** (Friendly & Fun)\n"
        "👨‍🏫 **Teacher** (Formal & Wise)\n\n"
        "Type **/mode** to switch personas!"
    )

async def mode_command_handler(client: Client, message: Message):
    """Shows buttons to switch modes"""
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍👧 Father", callback_data="mode_father"), InlineKeyboardButton("🤱 Mother", callback_data="mode_mother")],
        [InlineKeyboardButton("🤛 Brother", callback_data="mode_brother"), InlineKeyboardButton("💁‍♀️ Sister", callback_data="mode_sister")],
        [InlineKeyboardButton("👨‍🏫 Teacher", callback_data="mode_teacher")]
    ])
    await message.reply("🎭 **Choose my personality:**", reply_markup=buttons)

async def chat_handler(client: Client, message: Message):
    chat_id = message.chat.id
    
    try:
        # Get User Mode
        user_mode = await get_user_mode(chat_id)
        
        if message.voice:
            await client.send_chat_action(chat_id, enums.ChatAction.RECORD_AUDIO)
            voice_bytes = bytes((await message.download(in_memory=True)).getbuffer())
            user_prompt = await transcribe_audio(voice_bytes)
            if not user_prompt:
                await message.reply("⚠️ Couldn't hear you.")
                return
            display_text = f"🎤 {user_prompt}"
        else:
            await client.send_chat_action(chat_id, enums.ChatAction.TYPING)
            user_prompt = message.text
            display_text = message.text

        # Search
        search_context = ""
        if any(x in user_prompt.lower() for x in ["news", "price", "weather", "latest"]):
            await client.send_chat_action(chat_id, enums.ChatAction.FIND_LOCATION)
            search_context = await perform_web_search(user_prompt)

        # Generate (Passing the User Mode)
        past_history = await get_history(chat_id)
        ai_text = await generate_with_fallback(past_history, user_prompt, user_mode, search_context)
        
        await add_history(chat_id, display_text, ai_text)

        # Graphics
        if "```mermaid" in ai_text:
            try:
                matches = re.findall(r"```mermaid(.*?)```", ai_text, re.DOTALL)
                if matches:
                    image_file, _ = await get_mermaid_image(matches[0].strip())
                    ai_text = re.sub(r"```mermaid(.*?)```", "", ai_text, flags=re.DOTALL).strip()
                    if image_file:
                        await client.send_photo(chat_id, photo=image_file, caption="**📍 Roadmap**")
            except: pass

        # Reply
        if message.voice:
            audio = text_to_audio(ai_text)
            if audio: await message.reply_voice(audio, caption=ai_text[:200])
            else: await message.reply(ai_text)
        else:
            await message.reply(ai_text, parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")

async def button_handler(client: Client, cb: CallbackQuery):
    if cb.data.startswith("mode_"):
        new_mode = cb.data.split("_")[1]
        await set_user_mode(cb.message.chat.id, new_mode)
        await clear_history(cb.message.chat.id)
        await cb.message.edit_text(f"✅ **Mode Switched to: {new_mode.capitalize()}!**\n\nI will now talk like your {new_mode}.")

def register_handlers(app: Client):
    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    app.add_handler(MessageHandler(mode_command_handler, filters.command("mode")))
    app.add_handler(MessageHandler(chat_handler, (filters.text | filters.voice) & ~filters.command(["start", "mode"])))
    app.add_handler(CallbackQueryHandler(button_handler))
