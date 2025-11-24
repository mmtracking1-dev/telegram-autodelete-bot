import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Chat, Message, Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    ContextTypes, filters
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DELETE_AFTER_SECONDS = int(os.getenv("DELETE_AFTER_SECONDS", "28800"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("autodelete")

def is_media_message(msg: Message) -> bool:
    return any([
        msg.photo, msg.document, msg.video, msg.audio, msg.voice,
        msg.animation, msg.sticker, msg.video_note,
        msg.contact, msg.location, msg.venue
    ])

async def schedule_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat

    if chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    if is_media_message(msg):
        return

    if not (msg.text or "").strip():
        return

    async def delayed_delete():
        try:
            await asyncio.sleep(DELETE_AFTER_SECONDS)
            await context.bot.delete_message(chat_id=chat.id, message_id=msg.message_id)
            log.info("DELETED | chat=%s msg=%s", chat.id, msg.message_id)
        except Exception as e:
            log.warning("DELETE FAIL | chat=%s msg=%s | %s", chat.id, msg.message_id, e)

    context.application.create_task(delayed_delete())
    log.info("ENQUEUED | chat=%s msg=%s delete in %ss",
             chat.id, msg.message_id, DELETE_AFTER_SECONDS)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"AutoDelete bot radi.\n"
        f"• Brisanje posle: {DELETE_AFTER_SECONDS}s\n"
        f"• Slike/PDF/video se NE brišu.\n"
        f"• Bot mora biti admin sa 'Delete messages'."
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN nije postavljen u .env")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), schedule_delete))

    log.info("Bot START (polling).")
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()