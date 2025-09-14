# mindmate_ai_super_app_final.py
# MindMate AI — Final, Polished Super App
# Save this file and run: python mindmate_ai_super_app_final.py
# Recommended packages:
#   gradio requests gtts textblob pillow nltk

import os
import re
import csv
import json
import random
import traceback
from datetime import datetime, date, timedelta
from collections import Counter, defaultdict

# Networking & NLP
import requests

try:
    from textblob import TextBlob
except Exception:
    TextBlob = None

# TTS
try:
    from gtts import gTTS
except Exception:
    gTTS = None

# UI
import gradio as gr

# ---------------------------
# Paths and data directories
# ---------------------------
BASE_DIR = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

JOURNAL_PATH = os.path.join(DATA_DIR, "journal.csv")
VJ_PATH = os.path.join(DATA_DIR, "visual_journal.csv")
STREAKS_PATH = os.path.join(DATA_DIR, "streaks.csv")

# ---------------------------
# Settings & helpers
# ---------------------------
SETTINGS = {
    "speak_emojis": False,
}

EMOJI_REGEX = re.compile(r'[^\w\s.,?!\'"\-]')

def clean_text_for_tts(text, speak_emojis=False):
    if speak_emojis:
        return text or " "
    return EMOJI_REGEX.sub("", (text or " "))

def text_to_speech(text, filename=None, slow=True):
    """
    Create TTS mp3 using gTTS (if installed).
    Return generated filepath or None if TTS unavailable.
    """
    if not text:
        return None
    if filename is None:
        filename = f"tts_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.mp3"
    filepath = os.path.join(DATA_DIR, filename)
    safe = clean_text_for_tts(text, speak_emojis=SETTINGS.get("speak_emojis", False))
    if gTTS is None:
        return None
    try:
        tts = gTTS(text=safe, lang="en", slow=bool(slow))
        tts.save(filepath)
        return filepath
    except Exception as e:
        print("TTS error:", e)
        return None

# ---------------------------
# CSV read/write helpers
# ---------------------------
def load_rows(path):
    rows = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                r = csv.reader(f)
                _ = next(r, None)
                for row in r:
                    rows.append(row)
        except Exception:
            pass
    return rows

def save_rows(path, header, rows):
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            for r in rows:
                w.writerow(r)
    except Exception as e:
        print("CSV save error:", e)

journal_history = [tuple(r) for r in load_rows(JOURNAL_PATH)]
visual_journal = [list(r) for r in load_rows(VJ_PATH)]
streak_rows = [list(r) for r in load_rows(STREAKS_PATH)]

# ---------------------------
# Curated content banks
# ---------------------------
CHATBOT_REPLIES = [
    "I hear you. Thank you for sharing that with me — that matters.",
    "That sounds difficult. Let's take one small step together: a slow breath now.",
    "You're doing your best in a tough moment. What is one tiny thing you could do next?",
    "It makes sense you'd feel this way. Would you like a short grounding exercise?",
    "You matter. Can I help you pick one gentle action for the next 10 minutes?",
    "You’re allowed to rest. What would a small, kind step for yourself look like?",
    "Let's name the feeling together — what label fits it right now?",
    "Sometimes focusing on one breath can open a small window of calm.",
    "This moment is temporary. One tiny choice now can change the next hour.",
    "You're not alone in this — thank you for telling me. Would journaling help?",
    "I notice a lot in your words. Let's simplify: one tiny thing to do next?",
    "Small steps matter. What's one reasonable step you can take after this chat?",
    "If you're tired, soft rest counts as a helpful action. Permission: allowed.",
    "You’ve handled hard things before — what strength did you use that time?",
    "I can support you with a short micro-plan. Would you like that?",
    "A short walk, a drink of water, or a five-minute stretch can help reset.",
    "Be kind to yourself — how would you comfort a friend in this moment?",
    "If you want, I can guide you through a calming breathing exercise now.",
    "Name one small achievement from today, even if it feels tiny.",
    "Let's create a gentle plan: two steps, low-effort — which one first?",
    "It’s okay to feel unsettled. You’re doing better than you think in this moment.",
    "If you're worried about tomorrow, let's create a simple plan for one task.",
    "Acknowledging how you feel is brave. You're not expected to have all the answers.",
    "Would you like a grounding prompt that uses your five senses?",
    "You’re allowed to pause. Short rests often protect longer-term progress.",
    "Choose one thing that brings you comfort — a warm drink, a soft song, a hug.",
    "Sometimes putting the worry on paper reduces its size. Want a writing prompt?",
    "If your energy is low, a 10-minute restorative break can restore clarity.",
    "You're more resilient than you feel right now. Let's find one supportive action.",
    "Would you like an affirmation you can say slowly for one minute?",
    "Can I help convert that thought into a small, practical next step?",
    "If perfection is blocking you, aim for 'good enough' instead of perfect.",
    "You're allowed to ask for help. Is there someone you trust who can support you?",
    "If you're feeling overwhelmed, let's try a ten-minute 'do one thing' rule.",
    "This feeling is valid — validation is the first step toward a small solution.",
    "Let's acknowledge the difficulty and choose one tiny thing to do next.",
    "If it helps, we can craft a short breathing routine to follow together.",
    "Try to name three things you can see around you — name them slowly.",
    "Even micro-choices shape momentum. Pick one tiny choice to act on now.",
    "You can be both gentle and productive. What's a kind next step?",
    "If you need a distraction, a short creative task could shift your mood.",
    "If you're anxious, longer exhales help — try exhale for six seconds.",
    "Sometimes a small ritual (tea, notebook) anchors you. Which one helps?",
    "I can help you build a short, manageable plan. Would that be useful?",
    "If you're grieving, small compassionate actions matter more than answers.",
    "You deserve support and rest — let's plan a soft next step.",
    "Do you want a short affirmation, a breathing guide, or a micro-plan now?",
    "It's okay to take things slowly — one minute at a time is still progress.",
    "Let's convert worry to a tiny experimental action: try one small test.",
    "If sleep is poor, a small wind-down routine tonight may help.",
    "You're allowed to feel conflicting emotions — both can be true at once.",
    "Would listing 3 things you did well help to shift perspective?",
    "If it helps, I can lighten the task list into 10-minute chunks.",
    "You don't have to fix everything at once. A small change today helps tomorrow.",
    "Focus on controlling what you can; release what you can't right now.",
    "If you're stuck, try a 'two minute tidy' — tidy one small corner and breathe.",
    "Try naming one worry and one counter-fact to reduce its power.",
    "Would a short guided prompt for reflection help you now?",
    "I can offer a supportive reframe for a thought if you'd like to share it.",
    "You are allowed to reduce pressure. Small boundaries create safety.",
    "If you feel criticism, treat yourself as you would a close friend.",
    "Small gestures of self-care are powerful — what's one small gesture for you?",
    "If you're worried about judgement, practice 'it's mine to try' language.",
    "Would a micro-plan (3 steps) for the next hour be helpful?",
    "If your energy is up, use it for a small constructive action now.",
    "Try to notice one positive detail in the present moment.",
    "It's okay to retry tomorrow — progress is rarely linear.",
    "You are worthy of kindness and calm — starting now matters.",
    "You can try one new habit for 7 days and reassess — small wins compound.",
    "If resilience feels low, recall a prior moment you coped well for evidence.",
    "Name one value and choose an action today that aligns with it.",
    "You might benefit from a 2-minute grounding practice right now.",
    "If you're unsure, try one low-cost experiment and observe the outcome.",
    "You deserve compassion not just outcomes. What helps you feel cared for?"
]

MOOD_REPLIES = [
    "Try a grounding exercise: name 5 things you can see, 4 you can touch, 3 you can hear.",
    "If low, a brief connection with a trusted person can help you feel less isolated.",
    "If anxious, try longer exhale breathing for five cycles and notice the body soften.",
    "Neutral days are steady — schedule a small joyful activity to brighten it.",
    "If stressed, break tasks into 10-minute blocks and do one clean start.",
    "Hydration + 90 seconds of natural light often shifts energy levels slightly."
]

DAILY_TIPS = [
    "Step outside for 90 seconds and soften your gaze across the distance.",
    "Write three things you’re grateful for today and why they matter.",
    "Set one tiny goal for the next hour and complete it — celebrate the finish.",
    "Drink a full glass of water slowly, noticing the temperature and taste.",
    "Do a two-minute tidy of one small area to reduce visual clutter.",
    "Play one comforting song and notice what it does in your body.",
    "Text one kind message to someone you care about.",
    "Walk for 10 minutes with no screens and notice your pace.",
    "Stretch your shoulders and chest for 60 seconds and breathe slowly.",
    "Make a short plan for tomorrow with one non-negotiable positive item.",
    "Practice three-count inhale, five-count exhale breathing for two minutes.",
    "Write a short compassion note to yourself: 1–2 sentences.",
    "Schedule 10 minutes of phone-free time as a reset.",
    "Name three things you did well this week, even tiny ones.",
    "Allow 20 minutes of restorative rest and step away from tasks.",
    "Create a small pre-sleep routine: dim lights, tea, one note of gratitude."
]

JOURNAL_REPLIES = [
    "Journal saved — you’ve honored this moment.",
    "Entry recorded. Small notes build meaningful patterns.",
    "Saved. Thank you for showing up for yourself."
]

GROWTH_REPLIES = [
    "Growth snapshot ready — identify one focus for the next week.",
    "Report generated. Celebrate one small, concrete win this week."
]

BREATHING_REPLIES = [
    "Inhale 4 • Hold 4 • Exhale 6 — repeat 6 cycles, relax shoulders.",
    "Try box breathing 4-4-4-4 for three cycles to ground quickly.",
    "Two-minute slow-exhale breathing: focus on lengthening the out-breath."
]

AFFIRMATIONS = [
    "I am doing my best, and that is enough today.",
    "Small steps compound — I celebrate each tiny effort.",
    "I give myself permission to rest and to try again."
]

EMERGENCY_REPLIES = [
    "If you are in immediate danger, please call your local emergency number now.",
    "If you might harm yourself, please contact local emergency services or a crisis line immediately."
]

COGNITIVE_REFRAMES = [
    "This feels true right now, yet there may be other explanations. What contradicts this thought?",
    "If a friend thought this, what would you say to them? Try that tone with yourself.",
    "Swap 'always'/'never' language for 'sometimes' to reduce all-or-nothing thinking.",
    "Break the thought into fact vs interpretation and question the evidence.",
    "Reframe: 'I tried; this attempt didn't go as planned; I can try another approach.'",
    "Try 'both/and' thinking: 'This is hard, and I can still find small wins.'",
    "Consider: will this matter in a month or a year? Recalibrate perspective."
]

MICRO_PLANS = [
    "Next 10 minutes: do one focused small task.",
    "20-minute walk, leave the phone behind if possible.",
    "Write one sentence for tomorrow's plan and close your journal."
]

VJ_REPLIES = [
    "Visual entry saved — images can show what words cannot.",
    "Saved. Revisit this image in one week to notice changes."
]

STREAK_REPLIES = [
    "Marked — small consistency builds momentum.",
    "Already marked today — nice consistency."
]

# ---------------------------
# Utility: random picker & data fetchers
# ---------------------------
def pick_random(lst):
    return random.choice(lst) if lst else ""

def get_latest_journal_entry():
    if not journal_history:
        return "No entries yet. Write your first one!"
    ts, text, mood, _ = journal_history[-1]
    return f"**Latest Entry ({ts}):**\nMood: {mood}\n{text[:120]}..."

def get_streak_summary():
    if not streak_rows:
        return "No streaks. Start tracking a habit!"
    by_task = defaultdict(set)
    for t, d in streak_rows:
        by_task[t].add(d)
    lines = []
    for t, dates in by_task.items():
        cur = 0
        d = date.today()
        while d.isoformat() in dates:
            cur += 1
            d = d - timedelta(days=1)
        if cur > 0:
            lines.append(f"• **{t}**: {cur} days")
    if not lines:
        return "No active streaks today."
    return "**Active Streaks:**\n" + "\n".join(lines)

# ---------------------------
# Feature implementations
# ---------------------------
def chatbot_response(user_input: str):
    ui = (user_input or "").strip()
    if not ui:
        reply = "Tell me in a sentence how you're feeling or what you're facing — I'm listening."
        return reply, text_to_speech(reply, slow=True)
    lower = ui.lower()
    if any(w in lower for w in ["anx", "worri", "scared", "fear", "panic"]):
        reply = pick_random([
            "I hear the worry in your words. Let's try a grounding step: name five things you can see.",
            "That sense of worry is heavy — try an extended exhale now: breathe out slowly for six counts.",
            "When anxiety spikes, focusing on the body helps. Would you like a 2-minute breathing guide?"
        ])
    elif any(w in lower for w in ["sad", "lonely", "down", "hopeless"]):
        reply = pick_random([
            "I'm sorry you're feeling this way — a small comforting plan might help. Would you like a gentle step?",
            "Feeling low is valid. Would you like to try a short reflective prompt or a tiny self-care idea?",
            "This sadness matters. Consider reaching out to one trusted person — connection often eases the load."
        ])
    elif any(w in lower for w in ["angry", "frustrat", "annoyed", "irritat"]):
        reply = pick_random([
            "Anger can be energizing and also tiring. Would a short grounding or movement help?",
            "Notice the body where the tension shows: shoulders, jaw, chest. A movement release often helps.",
            "Let's turn the feeling into a small practical action — what's one step that might reduce friction?"
        ])
    else:
        reply = pick_random(CHATBOT_REPLIES)
    audio = text_to_speech(reply, slow=True)
    return reply, audio

def analyze_mood(text: str):
    t = (text or "")[:800]
    polarity = 0.0
    if TextBlob is not None and t.strip():
        try:
            polarity = TextBlob(t).sentiment.polarity
        except Exception:
            polarity = 0.0
    if polarity > 0.25:
        mood = "positive"
        color = "#e8fff6"
    elif polarity < -0.25:
        mood = "sad"
        color = "#eef6ff"
    else:
        mood = "neutral"
        color = "#f6efff"
    reply = pick_random(MOOD_REPLIES)
    audio = text_to_speech(reply, slow=True)
    return reply, color, audio, mood

def daily_tip():
    tip = pick_random(DAILY_TIPS)
    audio = text_to_speech(tip, slow=True)
    return tip, audio

def journal_entry(text: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    polarity = 0.0
    if TextBlob is not None and text:
        try:
            polarity = TextBlob(text[:1000]).sentiment.polarity
        except Exception:
            polarity = 0.0
    mood = "neutral"
    if polarity > 0.25:
        mood = "happy"
    elif polarity < -0.25:
        mood = "sad"
    journal_history.append((ts, text or "", mood, str(float(polarity))))
    save_rows(JOURNAL_PATH, ["timestamp","text","mood","polarity"], journal_history)
    reply = pick_random(JOURNAL_REPLIES)
    audio = text_to_speech(reply, slow=True)
    return reply, audio, gr.Markdown(value=get_latest_journal_entry())

def show_journal():
    if not journal_history:
        msg = "No journal entries yet. Try writing two honest sentences."
        return msg, text_to_speech(msg, slow=True)
    lines = [f"**{ts}** • Mood: {m}\n{t}" for ts, t, m, _ in journal_history[-200:]]
    msg = "\n\n".join(lines)
    audio = text_to_speech(pick_random(JOURNAL_REPLIES), slow=True)
    return msg, audio

def export_journal():
    if not os.path.exists(JOURNAL_PATH):
        save_rows(JOURNAL_PATH, ["timestamp","text","mood","polarity"], [])
    return JOURNAL_PATH

def growth_report():
    if not journal_history:
        msg = "No data yet — add a few journal entries to generate a Growth Report."
        return msg, text_to_speech(msg, slow=True)
    pols = [float(p) for _, _, _, p in journal_history]
    avg = sum(pols) / len(pols)
    trend = "rising 📈" if avg > 0.15 else ("dipping 📉" if avg < -0.15 else "steady ➡️")
    words = []
    STOPWORDS = set("a an the and or but if while to from of in on for with at by is it this that these those am are was were be been being i me my we our you your he she they them their as".split())
    for _, text, _, _ in journal_history:
        for w in re.findall(r"[A-Za-z']+", (text or "").lower()):
            if w not in STOPWORDS and len(w) > 2:
                words.append(w)
    common = ", ".join([w for w,_ in Counter(words).most_common(6)]) if words else "—"
    if avg < -0.15:
        goals = ["Text one supportive person", "Take a 5 min breathing break", "Write one compassionate sentence"]
    elif avg > 0.15:
        goals = ["Repeat a helpful habit", "Do a small act of kindness", "Try a mini-challenge"]
    else:
        goals = ["Plan a 10-min walk", "Quick tidy up", "List 3 tiny wins"]
    msg = (
        "### Daily Growth Report ✨\n"
        f"**Mood trend:** {trend}\n"
        f"**Common themes:** {common}\n"
        "**3 Focus Goals:**\n"
        f"1. {goals[0]}\n"
        f"2. {goals[1]}\n"
        f"3. {goals[2]}"
    )
    audio = text_to_speech(pick_random(GROWTH_REPLIES), slow=True)
    return msg, audio

def breathing_exercise():
    r = pick_random(BREATHING_REPLIES)
    audio = text_to_speech(r, slow=True)
    return r, audio

def affirmation():
    a = pick_random(AFFIRMATIONS)
    audio = text_to_speech(a, slow=True)
    return a, audio

def emergency_help():
    r = pick_random(EMERGENCY_REPLIES)
    audio = text_to_speech(r, slow=True)
    return r, audio

def cognitive_reframe(automatic_thought):
    thought = (automatic_thought or "").strip()
    if not thought:
        msg = "Please enter the automatic thought you'd like to reframe."
        return msg, text_to_speech(msg, slow=True)
    refr = pick_random(COGNITIVE_REFRAMES)
    short = (thought[:120] + "...") if len(thought) > 120 else thought
    msg = f"**Thought:** \"{short}\"\n**Reframe suggestion:**\n{refr}"
    audio = text_to_speech(msg, slow=True)
    return msg, audio

def micro_plan(prompt_text):
    base = pick_random(MICRO_PLANS)
    plan = f"**Micro-plan:** {base}\nTry: {base.split('.')[0]}."
    audio = text_to_speech(plan, slow=True)
    return plan, audio

def vjournal_add(image, caption):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    img_path = ""
    if image:
        img_path = image if isinstance(image, str) else getattr(image, "name", "")
    visual_journal.append([ts, img_path, caption or ""])
    save_rows(VJ_PATH, ["timestamp","image_path","caption"], visual_journal)
    reply = pick_random(VJ_REPLIES)
    audio = text_to_speech(reply, slow=True)
    return f"**{reply}** ({ts})", audio

def vjournal_show():
    if not visual_journal:
        return "No visual entries yet.", text_to_speech("No visual entries yet.", slow=True)
    lines = [f"**{ts}** • {os.path.basename(img) if img else '[no image]'} — {cap[:120]}" for ts, img, cap in visual_journal[-200:]]
    return "\n".join(lines), text_to_speech("Showing recent visual entries.", slow=True)

def vjournal_export():
    if not os.path.exists(VJ_PATH):
        save_rows(VJ_PATH, ["timestamp","image_path","caption"], [])
    return VJ_PATH

def streak_mark(task_name):
    task = (task_name or "").strip()
    if not task:
        return "Enter a task name to mark a streak.", text_to_speech("Enter a task name to mark a streak.", slow=True), gr.Markdown(value=get_streak_summary())
    today_iso = date.today().isoformat()
    for row in streak_rows:
        if row[0] == task and row[1] == today_iso:
            return f"Already marked today for '{task}'.", text_to_speech(pick_random(STREAK_REPLIES), slow=True), gr.Markdown(value=get_streak_summary())
    streak_rows.append([task, today_iso])
    save_rows(STREAKS_PATH, ["task","date"], streak_rows)
    return f"Marked '{task}' for today ({today_iso}).", text_to_speech(pick_random(STREAK_REPLIES), slow=True), gr.Markdown(value=get_streak_summary())

def streaks_status():
    if not streak_rows:
        return "No streaks yet. Create one by entering a task name and marking today.", text_to_speech("No streaks yet.", slow=True)
    by_task = defaultdict(set)
    for t, d in streak_rows:
        by_task[t].add(d)
    lines = []
    momentum_scores = []
    for t, dates in by_task.items():
        cur = 0
        d = date.today()
        while d.isoformat() in dates:
            cur += 1
            d = d - timedelta(days=1)
        longest = 0
        sorted_dates = sorted(dates)
        if sorted_dates:
            consec = 1
            for i in range(1, len(sorted_dates)):
                prev = datetime.fromisoformat(sorted_dates[i-1]).date()
                curr = datetime.fromisoformat(sorted_dates[i]).date()
                if (curr - prev).days == 1:
                    consec += 1
                else:
                    longest = max(longest, consec)
                    consec = 1
            longest = max(longest, consec)
        lines.append(f"• **{t}** — current: {cur} days, longest: {longest} days")
        momentum_scores.append(min(cur, longest))
    if momentum_scores:
        momentum = sum(momentum_scores) / (len(momentum_scores) * max(1, max(momentum_scores)))
        momentum_pct = int(momentum * 100)
    else:
        momentum_pct = 0
    msg = "**Your Momentum:**\n" + "\n".join(lines) + f"\n\n**Total Momentum Score:** {momentum_pct}%"
    audio = text_to_speech(f"Streaks status. Momentum {momentum_pct} percent.", slow=True)
    return msg, audio

def streaks_export():
    if not os.path.exists(STREAKS_PATH):
        save_rows(STREAKS_PATH, ["task","date"], [])
    return STREAKS_PATH

# ---------------------------
# UI CSS: fixed dark theme with animations
# ---------------------------
GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css');

:root {
    --bg-color: #0b0f12;
    --card-bg-color: #0f1417;
    --text-color: #e8eef6;
    --accent1: #7C5CFF;
    --accent2: #60C8F3;
    --main-title-color: #7C5CFF;
    --sub-text-color: #94a3b8;
}

body {
    font-family: 'Poppins', system-ui, -apple-system, 'Segoe UI', Roboto, Arial;
    margin: 0;
    padding: 0;
    background: var(--bg-color);
    color: var(--text-color);
    -webkit-font-smoothing: antialiased;
}

.app-inner {
    max-width: 1200px;
    margin: 0 auto;
    padding: 28px;
    transition: all 0.5s ease;
}

.header-title {
    text-align: center;
    margin-bottom: 24px;
    animation: fadeInDown 1s ease-in-out;
}

.header-title .main-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 80px;
    font-weight: 900;
    letter-spacing: 2px; /* Fixed spacing */
    color: var(--main-title-color);
    text-shadow: 0 8px 24px rgba(124,92,255,0.2);
    margin: 0;
    animation: textPop 0.8s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}

.header-title .subtitle {
    color: var(--sub-text-color);
    margin-top: -10px;
    font-size: 1.2em;
    animation: fadeIn 1.2s ease-in-out;
}

.card, .gradio-container .gr-form, .gradio-container .gr-textbox {
    border-radius: 18px !important;
    background: var(--card-bg-color) !important;
    padding: 24px;
    box-shadow: 0 16px 40px rgba(20,20,30,0.06);
    border: none !important;
    color: var(--text-color) !important;
    animation: cardFadeIn 1s ease-out;
    transition: background 0.3s ease, box-shadow 0.3s ease;
}

.gradio-container .gr-markdown, .gradio-container .gr-textbox textarea {
    background: var(--card-bg-color) !important;
    color: var(--text-color) !important;
}

.pill-tabs .gr-button {
    background: transparent !important;
    border-radius: 10px;
    border: none !important;
    color: var(--text-color) !important;
    font-weight: 600;
    transition: all 0.3s ease;
}

.pill-tabs .gr-button.selected {
    background: rgba(255,255,255,0.05) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(255,255,255,0.05);
}

.big-btn {
    background: linear-gradient(90deg,var(--accent1) 0%, var(--accent2) 100%);
    color:white;
    border:none;
    padding: 14px 24px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 1.1em;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: buttonPop 0.5s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}
.big-btn:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 18px 45px rgba(92,70,200,0.2);
}

.dashboard-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
}

/* Animations */
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes textPop {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes cardFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes buttonPop {
    from { transform: scale(0.9); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

.footer {
    text-align: center;
    margin-top: 40px;
    color: var(--sub-text-color);
    font-size: 14px;
}
"""
# ---------------------------
# Build Gradio UI
# ---------------------------
with gr.Blocks(css=GLOBAL_CSS, title="MindMate AI — A Super App for Mental Wellness") as demo:
    with gr.Column(elem_classes="app-inner"):
        # Header
        header_html = gr.HTML(value=(
            "<div class='header-title'>"
            "<div class='main-title'>MINDMATE AI</div>"
            "<div class='subtitle'>A vibrant and supportive companion for daily wellbeing</div>"
            "</div>"
        ))
        
        # User settings
        with gr.Row():
            speak_emojis_cb = gr.Checkbox(label="Let TTS speak emojis", value=False)
            status_box = gr.Textbox(value="Ready", label="Status", interactive=False, container=False)
            
            def apply_settings(speak_emojis_val):
                SETTINGS["speak_emojis"] = bool(speak_emojis_val)
                status = "Settings applied."
                audio = text_to_speech(status, slow=True)
                return status, audio
            
            gr.Button("Apply Settings", elem_classes="big-btn").click(
                fn=apply_settings, inputs=[speak_emojis_cb], outputs=[status_box, gr.Audio()]
            )
        
        # Tabs
        with gr.Tabs(elem_classes="pill-tabs"):
            with gr.TabItem("🏠 Dashboard"):
                with gr.Row(elem_classes="dashboard-grid"):
                    with gr.Column(scale=2):
                        gr.Markdown("### Welcome to your MindMate Dashboard! ✨")
                        gr.Markdown(
                            f"<div class='card' style='padding:14px; text-align:center;'><b>Daily Tip:</b><br>{daily_tip()[0]}</div>"
                        )
                        home_mood_in = gr.Textbox(label="How are you feeling right now?", placeholder="e.g., A bit stressed about work.")
                        home_mood_btn = gr.Button("Analyze Mood & Get Support")
                        home_mood_out = gr.Textbox(label="MindMate's Insight", lines=2)
                    with gr.Column(scale=1):
                        gr.Markdown("<div class='card'>**Your Progress at a Glance**</div>")
                        home_streak_out = gr.Markdown(get_streak_summary())
                        home_journal_out = gr.Markdown(get_latest_journal_entry())
            
            with gr.TabItem("💬 Chatbot"):
                with gr.Row():
                    with gr.Column(scale=2):
                        chatbot_input = gr.Textbox(label="Tell me how you feel or what you're facing...", lines=6, placeholder="e.g., I'm feeling anxious about exams")
                        chat_out = gr.Textbox(label="MindMate Reply", lines=8, show_copy_button=True, container=True)
                    with gr.Column(scale=1):
                        gr.Markdown(
                            """
                            <div class='card' style='padding:14px; text-align:center;'>
                                <div style='font-weight:700; font-size: 1.2em;'>💡 Quick Tools</div>
                                <div style='margin-top:8px;color:#94a3b8;'>Try a micro-plan, a reframe, or a breathing guide to start.</div>
                            </div>
                            """
                        )
                        chat_btn = gr.Button("Get Support 💖", elem_classes="big-btn")
                        chat_audio = gr.Audio(label="Voice Reply", autoplay=False)
                        gr.Markdown("---")
                        btn_breath = gr.Button("🌬️ Breathing Guide")
                        cog_btn = gr.Button("🧠 Reframe Thought")
                        plan_btn = gr.Button("🗺️ Create Micro-plan")

            with gr.TabItem("🔍 Mood Analyzer"):
                with gr.Row():
                    with gr.Column(scale=2):
                        mood_in = gr.Textbox(label="Type how you feel...", lines=4)
                        mood_out = gr.Textbox(label="Detected Mood & Suggestions", lines=6, interactive=False)
                        mood_btn = gr.Button("Analyze Mood ✨", elem_classes="big-btn")
                    with gr.Column(scale=1):
                        mood_color = gr.Textbox(label="Palette Hint", interactive=False)
                        mood_audio = gr.Audio(label="Voice Reply", autoplay=False)
                        gr.Markdown(
                            """
                            <div class='card' style='padding:14px; text-align:center;'>
                                <div style='font-weight:700; font-size: 1.2em;'>🎨 Mood-adaptive UI</div>
                                <div style='margin-top:8px;color:#94a3b8;'>The UI will adapt color hints based on your detected mood.</div>
                            </div>
                            """
                        )
            with gr.TabItem("📔 Journal"):
                with gr.Row():
                    with gr.Column(scale=2):
                        j_in = gr.Textbox(label="Write your thoughts...", lines=6, placeholder="Start your first entry here...")
                        j_out = gr.Textbox(label="Result", lines=2, interactive=False)
                        j_save = gr.Button("Save Entry 🖊️", elem_classes="big-btn")
                    with gr.Column(scale=1):
                        hist_btn = gr.Button("Show Recent Journal Entries 📖")
                        hist_out = gr.Markdown(value="<div style='color:#94a3b8;'>Start writing to see your history here.</div>", label="Journal History")
                        j_audio = gr.Audio(label="Voice Reply", autoplay=False)
                with gr.Row():
                    j_export_btn = gr.Button("Export Journal (.csv)")
                    j_export_file = gr.File(label="Download Journal (.csv)", interactive=False)

            with gr.TabItem("📈 Growth Report"):
                with gr.Row():
                    gr_btn = gr.Button("Generate Growth Report 🚀", elem_classes="big-btn")
                    gr_audio = gr.Audio(label="Voice Reply", autoplay=False)
                with gr.Row():
                    gr_out = gr.Markdown(label="Growth Report", value="<div style='color:#94a3b8;'>Your personal insights will appear here after you save a few journal entries.</div>")

            with gr.TabItem("🌞 Daily Tip"):
                with gr.Row():
                    tip_out = gr.Textbox(label="Your Tip for Today", lines=3, interactive=False)
                    tip_audio = gr.Audio(label="Voice Reply", autoplay=False)
                    tip_btn = gr.Button("Get a Tip ✨", elem_classes="big-btn")
            
            with gr.TabItem("🌈 Affirmations"):
                with gr.Row():
                    aff_out = gr.Textbox(label="Affirmation", lines=2, interactive=False)
                    aff_audio = gr.Audio(label="Voice Reply", autoplay=False)
                    aff_btn = gr.Button("Get Affirmation 💖", elem_classes="big-btn")
            
            with gr.TabItem("🚨 Emergency Help"):
                with gr.Row():
                    help_out = gr.Textbox(label="Emergency Guidance (non-medical)", lines=6, interactive=False)
                    help_audio = gr.Audio(label="Voice Reply", autoplay=False)
                    help_btn = gr.Button("Show Emergency Info 🆘", elem_classes="big-btn")
            
            with gr.TabItem("🧠 Cognitive Reframing"):
                with gr.Row():
                    cog_in = gr.Textbox(label="Automatic thought to reframe", lines=3, placeholder="e.g., I'm a failure.")
                    cog_out = gr.Markdown(label="Reframe", value="<div style='color:#94a3b8;'>Enter a thought above to challenge it.</div>")
                    cog_audio = gr.Audio(label="Voice Reply", autoplay=False)
                    cog_btn_reframe = gr.Button("Reframe Thought 💡", elem_classes="big-btn")

            with gr.TabItem("🗺️ Micro-plan"):
                with gr.Row():
                    plan_in = gr.Textbox(label="What's your immediate need?", lines=3, placeholder="e.g., need focus for 30 minutes")
                    plan_out = gr.Markdown(label="Micro-plan", value="<div style='color:#94a3b8;'>Generate a small, manageable plan for your next steps.</div>")
                    plan_audio = gr.Audio(label="Voice Reply", autoplay=False)
                    plan_btn_create = gr.Button("Create Micro-plan 🗓️", elem_classes="big-btn")

            with gr.TabItem("🎨 Visual Journal"):
                with gr.Row():
                    with gr.Column(scale=1):
                        v_img = gr.Image(label="Upload an image (optional)", type="filepath")
                        v_caption = gr.Textbox(label="Caption (what does this image mean to you?)", lines=2)
                        v_add = gr.Button("Add Visual Entry 🖼️", elem_classes="big-btn")
                        v_res = gr.Textbox(label="Result", lines=2, interactive=False)
                        v_audio = gr.Audio(label="Voice Reply", autoplay=False)
                    with gr.Column(scale=1):
                        v_show = gr.Button("Show Visual Journal 📸")
                        v_list = gr.Textbox(label="Recent Visual Entries", lines=8, interactive=False)
                        v_export = gr.Button("Export Visual Journal (.csv)")
                        v_export_file = gr.File(label="Download Visual Journal (.csv)", interactive=False)

            with gr.TabItem("📈 Streaks & Momentum"):
                with gr.Row():
                    with gr.Column(scale=1):
                        streak_task = gr.Textbox(label="Streak Task (e.g., Meditate)", lines=1, placeholder="Your habit name here...")
                        streak_mark_btn = gr.Button("Mark Today ✅", elem_classes="big-btn")
                        streak_status = gr.Textbox(label="Status", lines=3, interactive=False)
                        streak_export_btn = gr.Button("Export Streaks (.csv)")
                        streak_export_file = gr.File(label="Download Streaks (.csv)", interactive=False)
                    with gr.Column(scale=1):
                        streaks_view = gr.Markdown(label="All streaks & momentum", value="<div style='color:#94a3b8;'>Mark a task above to see your momentum grow.</div>")
                        streak_view_btn = gr.Button("View Streaks & Momentum 🔥")
                        streak_audio = gr.Audio(label="Voice Reply", autoplay=False)

        # Footer
        footer = gr.HTML("<div class='footer'>Built by MOHD. IMAD • Designed for a calm and powerful experience • 🚀 🌸</div>")

    # ---------------------------
    # Wiring: event handlers
    # ---------------------------
    home_mood_btn.click(analyze_mood, inputs=[home_mood_in], outputs=[home_mood_out, gr.Textbox(visible=False), gr.Audio(visible=False), gr.Textbox(visible=False)])
    j_save.click(journal_entry, inputs=[j_in], outputs=[j_out, j_audio, home_journal_out])
    streak_mark_btn.click(streak_mark, inputs=[streak_task], outputs=[streak_status, streak_audio, home_streak_out])

    def _chat_run(inp):
        try:
            out, audio = chatbot_response(inp)
            return out, audio
        except Exception:
            traceback.print_exc()
            fallback = "An error occurred. I'm sorry."
            return fallback, text_to_speech(fallback, slow=True)
    chat_btn.click(_chat_run, inputs=[chatbot_input], outputs=[chat_out, chat_audio])
    btn_breath.click(lambda: breathing_exercise(), None, [chat_out, chat_audio])
    cog_btn.click(lambda: (pick_random(COGNITIVE_REFRAMES), text_to_speech(pick_random(COGNITIVE_REFRAMES), slow=True)), None, [chat_out, chat_audio])
    plan_btn.click(lambda: micro_plan(None), None, [chat_out, chat_audio])

    def _mood_run(txt):
        try:
            out, color, audio, mood = analyze_mood(txt)
            return out, audio, f"Color: {color} • Mood: {mood}"
        except Exception:
            traceback.print_exc()
            return "Error analyzing mood.", None, ""
    mood_btn.click(_mood_run, inputs=[mood_in], outputs=[mood_out, mood_audio, mood_color])

    tip_btn.click(lambda: daily_tip(), None, [tip_out, tip_audio])
    hist_btn.click(show_journal, None, [hist_out, j_audio])
    j_export_btn.click(lambda: export_journal(), None, j_export_file)
    gr_btn.click(lambda: growth_report(), None, [gr_out, gr_audio])
    aff_btn.click(lambda: affirmation(), None, [aff_out, aff_audio])
    help_btn.click(lambda: emergency_help(), None, [help_out, help_audio])
    cog_btn_reframe.click(cognitive_reframe, inputs=[cog_in], outputs=[cog_out, cog_audio])
    plan_btn_create.click(micro_plan, inputs=[plan_in], outputs=[plan_out, plan_audio])
    v_add.click(vjournal_add, inputs=[v_img, v_caption], outputs=[v_res, v_audio])
    v_show.click(vjournal_show, None, [v_list, v_audio])
    v_export.click(lambda: vjournal_export(), None, v_export_file)
    streak_view_btn.click(streaks_status, None, [streaks_view, streak_audio])
    streak_export_btn.click(lambda: streaks_export(), None, streak_export_file)

# ---------------------------
# Launch logic (choose free port)
# ---------------------------
def find_free_port(preferred=7860):
    import socket
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", preferred))
        s.close()
        return preferred
    except OSError:
        s.close()
        s2 = socket.socket()
        s2.bind(("127.0.0.1", 0))
        port = s2.getsockname()[1]
        s2.close()
        return port

if __name__ == "__main__":
    port = find_free_port(7860)
    print(f"Launching MindMate AI on http://127.0.0.1:{port}")
    demo.launch(server_name="127.0.0.1", server_port=port, share=False)