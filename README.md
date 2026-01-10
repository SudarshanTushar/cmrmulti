# 🤖 AI Career Guidance Chatbot - Your Personal Career Advisor

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots/api)
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-green.svg)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **🎯 Your AI-Powered Career Guidance Companion - Get Personalized Career Advice, Skill Development Plans, and Professional Growth Strategies! 🎯**

## 📋 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Installation](#️-installation)
- [🔧 Configuration](#-configuration)
- [📱 Commands Reference](#-commands-reference)
- [💬 How to Use](#-how-to-use)
- [🏗️ Project Structure](#️-project-structure)
- [🛠️ Development](#️-development)
- [📝 License](#-license)

## ✨ Features

### 🎯 Core Features

- **AI Career Counseling** - Intelligent career advice powered by Gemini AI
- **Personalized Guidance** - Tailored recommendations based on your background and goals
- **Interactive Conversations** - Natural language career discussions
- **Skill Assessment** - Identify strengths and areas for improvement
- **Career Path Exploration** - Discover suitable career options

### 🔧 Advanced Features

- **Industry Insights** - Current job market trends and salary information
- **Learning Paths** - Structured skill development recommendations
- **Resume Optimization** - Professional resume and LinkedIn advice
- **Interview Preparation** - Practice questions and tips
- **Networking Strategies** - Professional connection building guidance

### 🤖 AI Assistant Features

- **Intelligent Q&A** - Ask detailed career-related questions
- **Contextual Responses** - Understands conversation history
- **Multi-language Support** - Career advice in multiple languages
- **Real-time Updates** - Current industry and job market information
- **Personalized Learning** - Adaptive recommendations based on interactions

### 👥 User Roles

- **👑 Owner** - Full bot control and management
- **🔧 Sudo Users** - Administrative assistance and monitoring
- **👤 Regular Users** - Career guidance and advice seekers

## 🚀 Quick Start

1. **Start Conversation** - Message the bot privately or in groups
2. **Ask Career Questions** - Use `/ask` for specific questions or just chat naturally
3. **Get Personalized Advice** - Receive tailored career guidance based on your background
4. **Explore Options** - Learn about different careers, skills, and industries
5. **Plan Your Future** - Get actionable steps for career development!

## ⚙️ Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB database (local or Atlas)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- Gemini AI API Key from [Google AI Studio](https://makersuite.google.com/app/apikey) (Required - for AI career guidance)

### Step-by-Step Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/career-guidance-bot.git
   cd career-guidance-bot
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**

   - Edit `config.py` with your credentials
   - Set up MongoDB connection
   - Configure bot settings

4. **Run the Bot**
   ```bash
   python bot.py
   ```

## 🔧 Configuration

### Edit `config.py`:

```python
# Telegram Bot Configuration
API_ID = your_api_id  # From https://my.telegram.org
API_HASH = "your_api_hash"  # From https://my.telegram.org
BOT_TOKEN = "your_bot_token"  # From @BotFather

# MongoDB Configuration
MONGO_URI = "your_mongodb_uri"  # MongoDB connection string

# Bot Owner Configuration
OWNER_ID = your_user_id  # Your Telegram user ID
SUDO_USERS = [user_id_1, user_id_2]  # Authorized administrators

# Gemini AI Configuration (Required - for AI career guidance)
GEMINI_API_KEY = "your_gemini_api_key"  # From https://makersuite.google.com/app/apikey
```

### Deploy to Heroku:

1. **Create Heroku App**

   ```bash
   heroku create your-quiz-bot
   ```

2. **Set Config Variables**

   ```bash
   heroku config:set API_ID=your_api_id
   heroku config:set API_HASH=your_api_hash
   heroku config:set BOT_TOKEN=your_bot_token
   heroku config:set MONGO_URI=your_mongodb_uri
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

## 📱 Commands Reference

### 🤖 AI Career Guidance Commands

| Command           | Description                     | Usage Example                       |
| ----------------- | ------------------------------- | ----------------------------------- |
| `/start`          | Show welcome message and help   | `/start`                            |
| `/help`           | Display available commands      | `/help`                             |
| `/ask <question>` | Ask the AI assistant anything   | `/ask What career should I choose?` |
| `/career <field>` | Get detailed career information | `/career software development`      |
| `/skills <role>`  | Learn required skills for a job | `/skills data scientist`            |

### 💬 Interactive Chat

- **Natural Conversation**: Just send any message for personalized career advice
- **Contextual Responses**: Reply to previous messages for follow-up guidance
- **Conversational AI**: The bot understands career-related discussions

### 👑 Admin Commands (Owner/Sudo Only)

| Command                | Description               | Usage Example                   |
| ---------------------- | ------------------------- | ------------------------------- |
| `/stats`               | View bot usage statistics | `/stats`                        |
| `/broadcast <message>` | Send message to all users | `/broadcast Maintenance notice` |

## 💬 How to Use

### Getting Started:

1. **Start a Conversation**

   - Send `/start` to see welcome message
   - Use `/help` for command reference

2. **Ask Career Questions**

   - Use `/ask` for specific questions: `/ask What skills do I need for UX design?`
   - Or just chat naturally: "I'm interested in technology careers"

3. **Get Specialized Advice**

   - `/career software` - Learn about software development careers
   - `/skills product manager` - See required skills for product management

   ```

   ```

4. **Customize Settings**

   ```
   /time 10  # Set 10-second delays
   ```

5. **End Quiz**
   ```
   /endquiz
   ```

### For Quiz Creators (Sudo Users):

1. **Create New Set**

   ```
   /new science_quiz
   ```

2. **Add Questions** (Multiple formats supported)

   ```
   Q) What is 2+2? A. Two B. Four C. Six D. Eight Answer: B. Four

   Q: What is H2O? || A) Hydrogen || B) Water || C) Oxygen || D) Carbon || Answer: B
   ```

3. **Save Questions**
   ```
   /save
   ```

### For Participants:

1. **Answer Questions**

   - Click on quiz poll options
   - Get instant feedback (✅/❌)
   - See poll statistics in real-time

2. **Check Personal Stats**
   ```
   /myanswer math_basics
   ```

### For AI Assistant Users (Owner & Sudo Users):

1. **Ask Questions & Get Help**

   ```
   /ask What is the theory of relativity?
   /ask Write a poem about programming
   /ask Translate "Hello World" to French
   /ask How to sort an array in Python?
   ```

2. **Generate Quiz Questions from Study Material**

   ```
   /generate 5 medium Photosynthesis is the process by which plants convert light energy into chemical energy using chlorophyll...
   ```

3. **Check AI Status**
   ```
   /aistatus
   ```

## 🏗️ Project Structure

```
career-guidance-bot/
├── bot.py                 # Main bot entry point
├── config.py              # Configuration settings
├── handlers.py            # Command and message handlers
├── db.py                 # Database operations (simplified)
├── gemini_ai.py          # AI career guidance assistant
├── utils.py              # Utility functions (if needed)
├── requirements.txt      # Python dependencies
├── Procfile             # Heroku deployment
├── runtime.txt          # Python version specification
└── README.md            # Project documentation
```

### Key Components:

- **`bot.py`** - Application entry point and client setup
- **`handlers.py`** - All command handlers and message processing
- **`gemini_ai.py`** - AI career guidance integration
- **`db.py`** - MongoDB operations and data management
- **`utils.py`** - Career guidance utility functions

## 🛠️ Development

### Dependencies

```python
# Core Framework
pyrogram>=2.0.0      # Telegram MTProto client
tgcrypto>=1.2.5      # Encryption for Pyrogram

# AI Integration
google-generativeai>=0.3.0  # Gemini AI for career guidance

# Database
pymongo>=4.0.0       # MongoDB driver
motor>=3.0.0         # Async MongoDB driver
dnspython>=2.0.0     # DNS resolution for MongoDB
```

### Database Schema

**Collections:**

- `user_conversations` - Conversation history for analytics
- `user_preferences` - User preference storage
- `bot_stats` - Usage statistics and metrics

### Key Features Implementation:

- **AI Career Counseling** - Gemini AI integration for intelligent responses
- **Conversational Interface** - Natural language processing for career questions
- **Personalized Guidance** - Context-aware career advice
- **Real-time Responses** - Async handlers for immediate AI responses
- **Permission System** - Role-based access control for admin features

### Local Development:

1. **Setup Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Configure Development Settings**

   - Use local MongoDB or MongoDB Atlas free tier
   - Create test bot with @BotFather
   - Get Gemini AI API key from Google AI Studio

3. **Run in Development Mode**
   ```bash
   python bot.py
   ```

### Contributing:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🔒 Security Features

- **Permission Validation** - Admin and sudo user verification
- **Input Sanitization** - Message content validation and filtering
- **API Key Protection** - Secure storage of Gemini AI credentials
- **Rate Limiting** - Built-in protection against spam and abuse
- **Conversation Logging** - Optional conversation history for improvement

## 📈 Performance

- **Async Operations** - Non-blocking I/O for better response times
- **AI Caching** - Intelligent response caching for common queries
- **Efficient Database Queries** - Optimized MongoDB operations
- **Modular Architecture** - Separated concerns for better maintainability
- **Fast AI Responses** - Optimized Gemini AI integration

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection Error**

   - Check MongoDB URI in config.py
   - Verify network connectivity
   - Ensure database permissions

2. **Bot Not Responding**

   - Verify bot token is correct
   - Check API_ID and API_HASH
   - Ensure bot has necessary permissions

3. **AI Not Working**
   - Verify Gemini API key is valid
   - Check API quota and limits
   - Ensure internet connectivity for AI requests

### Debug Mode:

Enable logging in `bot.py` for detailed error information:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

- **Developer**: [@Forever_Crush](https://t.me/Forever_Crush)
- **Version**: 1.0 (Career Guidance Edition)
- **Support**: Contact through Telegram
- **Issues**: [GitHub Issues](https://github.com/yourusername/career-guidance-bot/issues)

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**💝 Made with love for career guidance seekers! 🎯**

⭐ **Star this repo if you found it helpful!** ⭐


⭐ **Star this repo if you found it helpful!** ⭐
