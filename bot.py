import os
import re
import tempfile
from pathlib import Path

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi!")

URL_REGEX = re.compile(
    r"https?://(?:www\.)?"
    r"(?:youtube\.com|youtu\.be|instagram\.com|"
    r"tiktok\.com|facebook\.com|fb\.watch|"
    r"x\.com|twitter\.com)/\S+",
    re.IGNORECASE,
)

user_urls = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 <b>LUTFULLO DOWNLOADER BOT</b>\n\n"
        "YouTube, Instagram, TikTok, Facebook va X "
        "havolasidan video yoki audio yuklab oling.\n\n"
        "🔗 Linkni yuboring:",
        parse_mode="HTML",
    )


async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_REGEX.search(text)

    if not match:
        await update.message.reply_text(
            "❌ Qo‘llab-quvvatlanadigan link topilmadi.\n\n"
            "YouTube, Instagram, TikTok, Facebook yoki X linkini yuboring."
        )
        return

    url = match.group(0)
    user_id = update.effective_user.id
    user_urls[user_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 VIDEO", callback_data="video"),
            InlineKeyboardButton("🎵 AUDIO", callback_data="audio"),
        ]
    ]

    await update.message.reply_text(
        "✅ Link qabul qilindi!\n\n"
        "Qaysi formatda yuklab beray?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_urls.get(user_id)

    if not url:
        await query.edit_message_text(
            "❌ Link topilmadi.\n\nQaytadan link yuboring."
        )
        return

    mode = query.data

    await query.edit_message_text(
        "⏳ Yuklanmoqda...\n\n"
        "Iltimos, kuting."
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            if mode == "audio":
                output = str(temp_path / "%(title).80s.%(ext)s")

                options = {
                    "format": "bestaudio/best",
                    "outtmpl": output,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }

            else:
                output = str(temp_path / "%(title).80s.%(ext)s")

                options = {
                    "format": "best[ext=mp4]/best",
                    "outtmpl": output,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "merge_output_format": "mp4",
                }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)

            files = list(temp_path.glob("*"))

            if not files:
                raise RuntimeError("Fayl yuklanmadi.")

            file_path = files[0]

            title = info.get("title", "LUTFULLO")
            caption = f"✅ <b>{title}</b>"

            if mode == "audio":
                with open(file_path, "rb") as audio_file:
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=audio_file,
                        caption=caption,
                        parse_mode="HTML",
                    )

            else:
                with open(file_path, "rb") as video_file:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=video_file,
                        caption=caption,
                        parse_mode="HTML",
                        supports_streaming=True,
                    )

    except Exception as e:
        print("ERROR:", repr(e))

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                "❌ Yuklab bo‘lmadi.\n\n"
                "Link ishlamasligi yoki sayt yuklashni "
                "cheklagan bo‘lishi mumkin."
            ),
        )

    finally:
        user_urls.pop(user_id, None)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_url
        )
    )

    print("🤖 LUTFULLO Downloader Bot ishga tushdi!")

    app.run_polling()


if __name__ == "__main__":
    main()
