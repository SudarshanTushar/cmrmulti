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
# Using the fastest model for real-time conversation
MODEL_LIST = [
    "Meta-Llama-3.1-70B-Instruct",
]

# --- 🧠 UNIFIED SYSTEM INTELLIGENCE (Problem Statement Aligned) ---
SYSTEM_PROMPT = """
You are 'Pathsetu', an AI Career Guardian for students.
Your mission: Bridge the gap between rural students and modern career opportunities.

### CORE OPERATING RULES:
1. **MULTILINGUAL ADAPTATION:** - DETECT the language of the user's prompt. 
   - REPLY IN THE EXACT SAME LANGUAGE. 
   - If the user speaks Hindi, you speak Hindi. If Marathi, you speak Marathi.
   - Do NOT force English unless the user asks.

2. **LOCALIZED INTELLIGENCE:**
   - When suggesting jobs, prioritize opportunities accessible to the user's likely location (or remote work).
   - Suggest low-cost, high-value skills (e.g., YouTube learning, free certifications) rather than expensive degrees.

3. **VISUAL ROADMAPS:**
   - If the user asks "How to become X?" or "Roadmap", you MUST generate a `mermaid` graph.
   - Use `graph TD` layout.
   - Visual Structure: [Current Skill] --> [Gap/Action] --> [New Skill] --> [Job].

4. **VOICE-FIRST BREVITY:**
   - Keep answers concise (under 100 words per section).
   - Use bullet points.
   - Avoid complex URLs or code blocks unless requested.

### CONTEXTUAL DATA:
Use [WEB_SEARCH_RESULTS] to provide real salary numbers and active job trends.
"""

# --- SEARCH ENGINE (Real-time Local Data) ---
def search_sync(query):
    try:
        # Adding "India" or "freshers" context can help localization if needed
        # but we keep it generic to allow user specificity.
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
            # Recognize text (Google Speech Recog automatically detects language often, 
            # but defaulting to generic helps)
            text = recognizer.recognize_google(recognizer.record(source))
            return text
    except:
        return None

async def get_mermaid_image(mermaid_code):
    try:
        # Clean cleanup of the mermaid code
        graph_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
        
        # Style injection for better readability on mobile
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
                return file_obj
