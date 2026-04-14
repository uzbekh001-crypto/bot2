import os
import yt_dlp
import asyncio
import uuid
import subprocess

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

try:
    from moviepy.editor import VideoFileClip
except:
    from moviepy import VideoFileClip


TOKEN = os.getenv("8733345750:AAEo2glt62-MWDJ45S1M5TFkUJJV7WWvM74")

# 🔥 SMART STORAGE
user_tasks = {}


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom 👋\n Yuklash uchun link yuboring 📥")


# ---------------- DOWNLOAD ----------------
def download_video(url, filename):
    folder = "downloads"
    os.makedirs(folder, exist_ok=True)

    ydl_opts = {
        'outtmpl': f'{folder}/{filename}.%(ext)s',
        'format': 'best',
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for f in os.listdir(folder):
        if filename in f:
            return os.path.join(folder, f)

    return None


# ---------------- MP3 ----------------
def convert_to_mp3(input_file):
    output_file = input_file.rsplit(".", 1)[0] + ".mp3"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "192k",
        output_file
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_file if os.path.exists(output_file) else None


# ---------------- CIRCLE (MOVIEPY) ----------------
def make_circle_video(input_file):
    output_file = input_file.rsplit(".", 1)[0] + "_circle.mp4"

    clip = VideoFileClip(input_file)

    w, h = clip.size
    size = min(w, h)

    clip = clip.crop(
        x_center=w / 2,
        y_center=h / 2,
        width=size,
        height=size
    ).resize((480, 480))

    clip.write_videofile(
        output_file,
        codec="libx264",
        audio_codec="aac",
        verbose=False,
        logger=None
    )

    return output_file if os.path.exists(output_file) else None


# ---------------- SMART CLEANUP ----------------
async def auto_delete(user_id):
    await asyncio.sleep(45)

    data = user_tasks.get(user_id)

    if not data:
        return

    file_path = data.get("file")

    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

    folder = "downloads"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, f))
            except:
                pass

    user_tasks.pop(user_id, None)


# ---------------- HANDLE MESSAGE ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except:
        pass

    url = update.message.text
    user_id = update.effective_user.id

    msg = await update.message.reply_text("⏳ Yuklanmoqda...")

    loop = asyncio.get_event_loop()
    filename = str(uuid.uuid4())

    file_path = await loop.run_in_executor(
        None,
        download_video,
        url,
        filename
    )

    if not file_path:
        return await msg.edit_text("❌ Video topilmadi")

    # 🔥 STORE TASK
    user_tasks[user_id] = {
        "file": file_path,
        "mp3_done": False,
        "circle_done": False
    }

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 MP3", callback_data="mp3"),
            InlineKeyboardButton("⭕ Circle", callback_data="circle"),
        ]
    ])

    with open(file_path, "rb") as video:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video,
            reply_markup=keyboard
        )

    await msg.delete()

    asyncio.create_task(auto_delete(user_id))


# ---------------- BUTTON HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_tasks:
        return await query.message.reply_text("❌ Video topilmadi")

    file_path = user_tasks[user_id]["file"]
    loop = asyncio.get_event_loop()

    # ---------------- MP3 ----------------
    if query.data == "mp3":

        msg = await query.message.reply_text("🎧 MP3 tayyorlanmoqda...")

        mp3_path = await loop.run_in_executor(
            None,
            convert_to_mp3,
            file_path
        )

        if mp3_path:
            with open(mp3_path, "rb") as audio:
                await context.bot.send_audio(
                    chat_id=query.message.chat.id,
                    audio=audio
                )

            try:
                os.remove(mp3_path)
            except:
                pass

            user_tasks[user_id]["mp3_done"] = True
            await msg.delete()
        else:
            await msg.edit_text("❌ MP3 ishlamadi")


    # ---------------- CIRCLE ----------------
    elif query.data == "circle":

        msg = await query.message.reply_text("⭕ Aylana video tayyorlanmoqda...")

        circle_path = await loop.run_in_executor(
            None,
            make_circle_video,
            file_path
        )

        if circle_path and os.path.exists(circle_path):

            await context.bot.send_video_note(
                chat_id=query.message.chat.id,
                video_note=open(circle_path, "rb")
            )

            try:
                os.remove(circle_path)
            except:
                pass

            user_tasks[user_id]["circle_done"] = True
            await msg.delete()
        else:
            await msg.edit_text("❌ Circle ishlamadi")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot ishladi 🚀")
    app.run_polling()










'''import os
import yt_dlp
import asyncio
import uuid
import subprocess

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "8733345750:AAEz-MyvSixyDlz2jURl2nn1mm6_KhIYDio"

user_data = {}


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom 👋\nLink yubor 📥")


# ---------------- DOWNLOAD ----------------
def download_video(url, filename):
    folder = "downloads"
    os.makedirs(folder, exist_ok=True)

    ydl_opts = {
        'outtmpl': f'{folder}/{filename}.%(ext)s',
        'format': 'best',
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for f in os.listdir(folder):
        if filename in f:
            return os.path.join(folder, f)

    return None


# ---------------- MP3 ----------------
def convert_to_mp3(input_file):
    output_file = input_file.rsplit(".", 1)[0] + ".mp3"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "192k",
        output_file
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_file if os.path.exists(output_file) else None


# ---------------- CLEAN ----------------
async def auto_delete(user_id, file_path):
    await asyncio.sleep(30)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

    folder = "downloads"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, f))
            except:
                pass

    user_data.pop(user_id, None)


# ---------------- HANDLE MESSAGE ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    except:
        pass

    url = update.message.text
    user_id = update.effective_user.id

    msg = await update.message.reply_text("⏳ Yuklanmoqda...")

    loop = asyncio.get_event_loop()
    filename = str(uuid.uuid4())

    file_path = await loop.run_in_executor(
        None,
        download_video,
        url,
        filename
    )

    if not file_path:
        return await msg.edit_text("❌ Video topilmadi")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 MP3 qilish", callback_data="mp3"),
            InlineKeyboardButton("⭕ Aylana video", callback_data="circle"),
        ]
    ])

    with open(file_path, "rb") as video:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=video,
            reply_markup=keyboard
        )

    await msg.delete()

    user_data[user_id] = file_path

    asyncio.create_task(auto_delete(user_id, file_path))


# ---------------- BUTTON ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_data:
        return await query.message.reply_text("❌ Video topilmadi")

    file_path = user_data[user_id]

    # ---------------- MP3 ----------------
    if query.data == "mp3":

        msg = await query.message.reply_text("🎧 MP3 tayyorlanmoqda...")

        loop = asyncio.get_event_loop()

        mp3_path = await loop.run_in_executor(
            None,
            convert_to_mp3,
            file_path
        )

        if mp3_path:
            with open(mp3_path, "rb") as audio:
                await context.bot.send_audio(
                    chat_id=query.message.chat.id,
                    audio=audio
                )

            try:
                os.remove(mp3_path)
                os.remove(file_path)
            except:
                pass

            user_data.pop(user_id, None)

            await msg.delete()
        else:
            await msg.edit_text("❌ MP3 ishlamadi")


    # ---------------- CIRCLE (TEMP SIMPLE) ----------------
    elif query.data == "circle":

        msg = await query.message.reply_text("⭕ Aylana video tayyorlanmoqda...")

        try:
            with open(file_path, "rb") as video:
                await context.bot.send_video_note(
                    chat_id=query.message.chat.id,
                    video_note=video
                )

            await msg.delete()

        except:
            await msg.edit_text("❌ Aylana video ishlamadi")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot ishladi 🚀")
    app.run_polling()'''