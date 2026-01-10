import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from handlers import register_handlers

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Starting Pathsetu Bot...")
    
    # Initialize Bot
    app = Client(
        "pathsetu_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True
    )
    
    # Load Handlers
    register_handlers(app)
    
    # Start Bot
    logger.info("✅ Bot is Online!")
    app.run()

if __name__ == "__main__":
    main()
