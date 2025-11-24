import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("autodelete")

# 🔥 Koliko sekundi poruka sme da stoji (promeni po želji)
DELETE_AFTER_SECONDS = int(os.getenv("DELETE_AFTER_SECONDS", "60"))

# 🔥 Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def schedule_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zakazuje brisanje poruke nakon DELETE_AFTER_SECONDS sekundi."""

    if context.job_queue is None:
        logger.error("JobQueue nije inicijalizovan!")
        return

    msg = update.message
    if not msg:
        return

    chat_id = msg.chat_id
    message_id = msg.message_id

    logger.info(f"Zakazujem brisanje: chat={chat_id}, msg={message_id}")

    context.job_queue.run_once(
        delete_message_job,
        when=DELETE_AFTER_SECONDS,
        chat_id=chat_id,
        name=f"del_{chat_id}_{message_id}",
        data={"message_id": message_id},
    )


async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    """Briše poruku koju smo zakazali."""
    job = context.job
    chat_id = job.chat_id
    message_id = job.data["message_id"]

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Obrisano: chat={chat_id}, msg={message_id}")
    except Exception as e:
        logger.error(f"Ne mogu da obrišem poruku {message_id}: {e}")


async def main():
    logger.info("Starting bot...")

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            schedule_delete,
        )
    )

    await application.run_polling(close_loop=False)


if __name__ == "__main__":
    asyncio.run(main())
