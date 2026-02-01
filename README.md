# 🇮🇳 Pathsetu: AI Career Guidance for Rural India

> **"Bridging the gap between rural students and modern career opportunities."**

Pathsetu is an AI-powered, multilingual Telegram bot designed to empower students in rural India. It provides personalized career pathways, localized job market insights, and visual roadmaps in their native language—breaking down barriers to professional growth.

## 🎯 Problem Statement
Rural students often lack access to career guidance and exposure to diverse job opportunities, leading to limited aspirations and higher dropout rates. Pathsetu bridges this gap by generating personalized career pathways based on user interests, local job markets, and skill gaps using LLMs, visual infographics, and voice interaction.

## ✨ Key Features

### 🗣️ 1. Native Multilingual Support
- **Auto-Detection:** Instantly detects if the user is speaking Hindi, Marathi, Telugu, etc.
- **Native Reply:** Responds in the **exact same language** to ensure complete understanding.
- **No Language Barrier:** Eliminates the "English-only" friction for rural users.

### 📊 2. Visual Career Roadmaps
- **Instant Visualization:** Converts text-based advice into visual flowcharts (Mermaid.js).
- **Gap Analysis:** Visually maps [Current Skill] → [Action Step] → [Goal].
- **Infographics:** Generates downloadable images for "How to become X" queries.

### 🎤 3. Voice-First Interaction
- **Speech-to-Text (STT):** Users can ask questions via voice notes (ideal for those less comfortable typing).
- **Text-to-Speech (TTS):** The bot replies with audio notes in the user's native language.
- **Concise Audio:** Responses are optimized for listening (short, bulleted, clear).

### 🌏 4. Localized Market Intelligence
- **Real-Time Search:** Fetches live data on salaries, job openings, and trends in India.
- **Accessible Opportunities:** Prioritizes low-cost learning paths (YouTube, free certifications) over expensive degrees.
- **Job Reality:** Provides factual salary data and demand analysis.

## 🛠️ Tech Stack

- **Core Framework:** Python 3.11+, Pyrogram (Telegram Client)
- **AI Engine:** Llama 3.1 70B (via SambaNova Cloud)
- **Database:** MongoDB (Motor AsyncIO)
- **Search:** DuckDuckGo Search (DDGS)
- **Voice Processing:** - `SpeechRecognition` (Google API) for STT
  - `gTTS` (Google Text-to-Speech) for TTS
  - `pydub` for audio conversion
- **Visualization:** `mermaid.ink` API

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- MongoDB Connection String
- Telegram Bot Token (from @BotFather)
- SambaNova API Key (for LLM)
- `ffmpeg` (Required for audio processing)

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/pathsetu-bot.git](https://github.com/yourusername/pathsetu-bot.git)
cd pathsetu-bot
```
### 2. Install Dependencies
```Bash

pip install -r requirements.txt
Note: You also need ffmpeg installed on your system.

Ubuntu/Debian: sudo apt install ffmpeg

Windows: Download and add to PATH.
```

Heroku: Add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git to your app's buildpacks.

### 3. Configuration
Edit config.py or set Environment Variables:

```Python

API_ID = "123456"               # Telegram API ID
API_HASH = "your_hash"          # Telegram API Hash
BOT_TOKEN = "your_bot_token"    # Telegram Bot Token
MONGO_URI = "mongodb+srv://..." # MongoDB Connection
SAMBANOVA_API_KEY = "xyz..."    # SambaNova AI Key
SAMBANOVA_BASE_URL = "[https://api.sambanova.ai/v1](https://api.sambanova.ai/v1)"
```
### 4. Run the Bash
```Bash

python bot.py
```
📱 Usage Guide
Start the Bot: Send /start to initialize.

Ask in Your Language:

User (Hindi Voice Note): "Mujhe software engineer banna hai, kya karun?"

Pathsetu (Hindi Audio + Text): Explains steps in Hindi + Generates a Roadmap Image.

Get a Roadmap:

Type: "Roadmap for Data Science"

Output: Returns a visual flowchart image.

Check Salaries:

Type: "Python Developer salary in India"

Output: Fetches real-time data from the web.

🤝 Contribution
We welcome contributions to make career guidance accessible to every student in India.

Fork the repo.

Create a feature branch gitt checkout -b feature/NewLanguage).

Commit changes.

Push and create a Pull Request.

📄 License
MIT License. Free to use for educational and non-profit initiatives.
