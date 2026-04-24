import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ==============================
# CONFIG
# ==============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)

# ==============================
# SYSTEM PROMPT (HUMAN STYLE)
# ==============================

SYSTEM_PROMPT = """
You are a compassionate and emotionally intelligent mental health assistant.

Speak like a real human in a natural conversation.

Rules:
- Do NOT use numbered points or lists
- Do NOT use headings like "Situation Insight"
- Be warm, empathetic, and supportive
- Keep responses conversational and flowing
- Avoid sounding robotic or clinical
- Keep responses clear and not too long

Focus on:
- Understanding feelings
- Offering gentle support
- Encouraging reflection naturally

Your goal is to connect, not to analyze.
"""

# ==============================
# COMMAND: /start
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey 😊 I'm here for you.\n\nTell me what's on your mind."
    )

# ==============================
# HANDLE MESSAGES
# ==============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
        )

        reply = response.choices[0].message.content

    except Exception as e:
        logging.error(f"Error: {e}")
        reply = "I'm having a small issue right now, but I'm still here with you. Try again in a moment 💛"

    await update.message.reply_text(reply)

# ==============================
# MAIN (NO WRAPPER)
# ==============================

print("RUNNING ADVANCED AI BOT")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()