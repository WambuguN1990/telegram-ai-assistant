import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# =========================
# CONFIG (SAFE)
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# MEMORY (simple JSON)
# =========================
MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    import json
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    import json
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

memory = load_memory()

# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """
You are a supportive mental health assistant helping Nicholas.

Structure every response like this:

1. Situation Insight
2. Possible Cause
3. Practical Action
4. Reflective Question

Keep tone warm, human, and supportive.
Avoid being robotic.
Keep responses clear and structured.
"""

# =========================
# COMMAND: /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "Nicholas"

    await update.message.reply_text(
        f"Hello {user_name} 👋\n"
        "I'm your mental health assistant.\n\n"
        "Tell me about a situation you're facing."
    )

# =========================
# MESSAGE HANDLER
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_text = update.message.text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Nicholas says: {user_text}"}
            ],
            temperature=0.7
        )

        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(reply)

# =========================
# RUN BOT (IMPORTANT FOR RAILWAY)
# =========================
print("RUNNING CLEAN AI BOT")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")

app.run_polling()