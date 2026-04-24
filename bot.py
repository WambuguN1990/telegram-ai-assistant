import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

MEMORY_FILE = "memory.json"


# =========================
# LOAD / SAVE MEMORY
# =========================
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)


memory = load_memory()


# =========================
# CURRENT DATE
# =========================
def get_current_datetime():
    return datetime.now().strftime("%A, %B %d, %Y %H:%M")


# =========================
# USER BACKGROUND CONTEXT
# =========================
USER_BACKGROUND = """
The user has the following background:

- Nurse trained in Germany (Ausbildung)
- Worked at St. Theresien Hospital Nürnberg and Uniklinik Erlangen
- 3+ years experience at Diakonie Neuendettelsau supporting adults with disabilities
- Studying Counseling Psychology at Africa Nazarene University (7th semester completed)
- Interested in neurocognitive psychology and learning sciences
- Applied for Master's at LMU Munich (awaiting feedback)

Use this ONLY when relevant to improve responses.
Do NOT repeat it unnecessarily.
"""


# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey 👋 I'm here for you.\n\nTell me what's on your mind."
    )


# =========================
# MAIN HANDLER
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_message = update.message.text
    timestamp = get_current_datetime()

    if user_id not in memory:
        memory[user_id] = []

    # Save user message
    memory[user_id].append({
        "role": "user",
        "message": user_message,
        "time": timestamp
    })

    # Keep last 10 messages
    history = memory[user_id][-10:]

    # =========================
    # SYSTEM PROMPT
    # =========================
    system_prompt = f"""
You are a calm, empathetic, and supportive mental health assistant.

STYLE:
- Speak naturally like a human
- No numbered lists
- No rigid formats
- Be warm, supportive, and conversational
- Keep responses clear and not too long

AWARENESS:
- Current date and time: {timestamp}
- If asked about today's date, use this EXACT value

USER CONTEXT:
{USER_BACKGROUND}
"""

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })

    # =========================
    # OPENAI CALL (FIXED MODEL)
    # =========================
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # ✅ FIXED MODEL
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content

    except Exception as e:
        print("FULL ERROR:", str(e))  # 👈 IMPORTANT DEBUG
        reply = "Something went wrong. Please try again."

    # Save bot reply
    memory[user_id].append({
        "role": "assistant",
        "message": reply,
        "time": timestamp
    })

    save_memory(memory)

    await update.message.reply_text(reply)


# =========================
# RUN BOT
# =========================
def main():
    print("RUNNING ADVANCED AI BOT...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()