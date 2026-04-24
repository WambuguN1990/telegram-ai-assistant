import os
import json
import asyncio
from datetime import datetime
from telegram import Update
from telegram.constants import ChatAction
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
# MEMORY SYSTEM
# =========================
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


memory = load_memory()


def get_time():
    return datetime.now().strftime("%A, %B %d, %Y %H:%M")


# =========================
# USER BACKGROUND
# =========================
USER_BACKGROUND = """
User background:
- Nurse trained in Germany
- Worked at St. Theresien Nürnberg & Uniklinik Erlangen
- 3 years at Diakonie Neuendettelsau
- Studying Counseling Psychology (Africa Nazarene University)
- Interested in Neurocognitive Psychology
- Applied to LMU Munich

Use ONLY when relevant.
"""


# =========================
# SAFE OPENAI CALL
# =========================
def ask_ai(messages):
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return res.choices[0].message.content
    except Exception as e:
        print("ERROR 1:", e)
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )
            return res.choices[0].message.content
        except Exception as e2:
            print("ERROR 2:", e2)
            return "I'm here with you — something glitched. Try again."


# =========================
# EMOTION DETECTION
# =========================
def detect_emotion(text):
    emotions = {
        "stress": ["stress", "tired", "overwhelmed"],
        "anxiety": ["anxious", "worried", "fear"],
        "sadness": ["sad", "down", "lonely"],
        "positive": ["happy", "good", "excited"]
    }

    for label, words in emotions.items():
        for w in words:
            if w in text.lower():
                return label
    return "neutral"


# =========================
# MEMORY SUMMARIZATION
# =========================
def summarize_history(user_id):
    history = memory[user_id][-20:]

    messages = [
        {"role": "system", "content": "Summarize this conversation briefly."}
    ]

    for h in history:
        messages.append({"role": h["role"], "content": h["message"]})

    summary = ask_ai(messages)
    memory[user_id] = [{"role": "system", "message": summary, "time": get_time()}]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey 👋 I'm here for you. What's on your mind?")


# =========================
# JOURNAL COMMAND
# =========================
async def journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id not in memory:
        await update.message.reply_text("No entries yet.")
        return

    entries = memory[user_id][-5:]
    text = "\n\n".join([f"{e['time']}\n{e['message']}" for e in entries])

    await update.message.reply_text("Your recent reflections:\n\n" + text)


# =========================
# MAIN HANDLER
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    now = get_time()

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    if user_id not in memory:
        memory[user_id] = []

    emotion = detect_emotion(text)

    memory[user_id].append({
        "role": "user",
        "message": text,
        "time": now,
        "emotion": emotion
    })

    # Long-term memory trigger
    if len(memory[user_id]) > 30:
        summarize_history(user_id)

    system_prompt = f"""
You are a supportive, human-like mental health assistant.

STYLE:
- Natural conversation
- No lists or structure
- Warm, calm, human

CONTEXT:
Time: {now}
Emotion detected: {emotion}

USER:
{USER_BACKGROUND}
"""

    messages = [{"role": "system", "content": system_prompt}]

    for m in memory[user_id][-10:]:
        messages.append({"role": m["role"], "content": m["message"]})

    reply = ask_ai(messages)

    memory[user_id].append({
        "role": "assistant",
        "message": reply,
        "time": now
    })

    save_memory(memory)

    await update.message.reply_text(reply)


# =========================
# RUN
# =========================
def main():
    print("RUNNING ADVANCED AI SYSTEM...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("journal", journal))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()


if __name__ == "__main__":
    main()