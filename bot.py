import os
import json
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from openai import OpenAI

# =========================
# CONFIG (SAFE)
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN environment variable")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# USER PERSONALIZATION
# =========================

USER_NAME = "Nicholas"

# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = f"""
You are a professional workplace mental health and care assistant.

You are currently speaking with {USER_NAME}.

Your role:
1. Analyze stress and emotional situations
2. Help reflect on workplace interactions
3. Support ethical caregiving practices
4. Document behavior professionally (without personal identifiers)

Rules:
- NEVER use names of clients or residents
- You MAY address the user as {USER_NAME} when appropriate
- Use neutral labels like "Resident A"
- Be structured and professional
- Keep responses clear and not too long
- Occasionally use the user's name naturally, but do not overuse it

Structure responses like:
1. Situation Insight
2. Possible Cause
3. Practical Action
4. Reflective Question
"""

# =========================
# MEMORY (OPTIONAL)
# =========================

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

memory = load_memory()

# =========================
# COMMAND: /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Hello {USER_NAME} 👋\nI'm your mental health assistant.\n\nSend me a situation you're dealing with."
    )

# =========================
# MESSAGE HANDLER
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    user_id = str(update.message.chat_id)

    # ✅ Simple greetings (no AI needed)
    if user_message.lower() in ["hi", "hello", "hey"]:
        await update.message.reply_text(
            f"Hello {USER_NAME} 👋\nTell me about a situation you're facing."
        )
        return

    try:
        # Save basic memory
        memory[user_id] = {
            "last_message": user_message,
            "time": str(datetime.now())
        }
        save_memory(memory)

        # AI response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
        )

        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(reply)

# =========================
# MAIN
# =========================

def main():
    print("RUNNING CLEAN AI BOT")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

# =========================

if __name__ == "__main__":
    main()