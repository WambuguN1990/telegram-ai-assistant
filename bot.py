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
# USER PROFILE CONTEXT
# =========================
USER_BACKGROUND = """
The user you are speaking to has the following background:

- A nurse trained in Germany (Ausbildung)
- Worked at St. Theresien Hospital Nürnberg and Uniklinik Erlangen
- Has 3+ years experience working with Diakonie Neuendettelsau supporting adults with disabilities
- Currently pursuing a Bachelor's degree in Counseling Psychology at Africa Nazarene University (7th semester completed)
- Interested in neurocognitive psychology, learning sciences, and human development
- Has applied for a Master's program at LMU Munich and is awaiting feedback

Use this information ONLY when relevant:
- To make responses more personalized
- To acknowledge academic or professional context
- To give more tailored advice

DO NOT:
- Repeat this information unnecessarily
- Mention it unless it adds real value to the response
"""


# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey 👋 I'm here for you.\n\nTell me what's on your mind."
    )


# =========================
# MESSAGE HANDLER
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

    history = memory[user_id][-10:]

    # =========================
    # SYSTEM PROMPT
    # =========================
    system_prompt = f"""
You are a calm, empathetic, and conversational mental health assistant.

COMMUNICATION STYLE:
- Speak naturally like a human
- No numbered lists
- No rigid structures like "Situation Insight"
- Be warm, grounded, and supportive
- Keep responses clear and not too long

AWARENESS:
- Current date and time: {timestamp}
- If asked about today's date, use this exact value

PERSONALIZATION CONTEXT:
{USER_BACKGROUND}
"""

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })

    # =========================
    # OPENAI CALL
    # =========================
    try:
        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content

    except Exception as e:
        reply = "Something went wrong. Please try again."
        print("ERROR:", e)

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