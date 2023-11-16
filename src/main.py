from telegram.ext import Application,CommandHandler,ContextTypes,ConversationHandler,MessageHandler,filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.error import NetworkError
from logic.admin_logic import admin_conversation_handler
from logic.user_logic import user_conversation_handler
import logging
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    print(f'Update {update} caused error {context.error}')

def run() -> None:
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(user_conversation_handler)
        application.add_handler(admin_conversation_handler)
        application.add_error_handler(error_handler)
        print('bot started')
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f'error starting bot: {e}')


if __name__ == "__main__":
    run()