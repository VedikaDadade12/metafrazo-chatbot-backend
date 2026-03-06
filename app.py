from flask import Flask, request, jsonify
import re

from languages.marathi import MARATHI
from languages.hindi import HINDI
from languages.english import ENGLISH

app = Flask(__name__)

# ======================================================
# LANGUAGE DATA
# ======================================================

LANGUAGES = {
    "marathi": MARATHI,
    "hindi": HINDI,
    "english": ENGLISH
}

LANGUAGE_LABELS = {
    "marathi": "Marathi 🇮🇳",
    "hindi": "Hindi 🇮🇳",
    "english": "English 🌍"
}

CURRENT_LANGUAGE = "english"

USER_SCORE = 0
USER_STREAK = 1

QUIZ_ACTIVE = False
QUIZ_CORRECT_OPTION = None
QUIZ_CORRECT_TEXT = None


# ======================================================
# UTILITIES
# ======================================================

def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower().strip())


def detect_language(text):
    """
    Detect Devanagari text automatically
    """
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hindi"
    return "english"


def smart_match(user_msg, key):

    user_msg = normalize(user_msg)
    key = normalize(key)

    if user_msg == key:
        return True

    if key in user_msg:
        return True

    key_words = key.split()

    return all(word in user_msg for word in key_words)


def search_category(data, category, msg):

    for key, value in data.get(category, {}).items():

        if smart_match(msg, key):
            return value

    return None


# ======================================================
# HEALTH CHECK
# ======================================================

@app.route("/")
def home():
    return jsonify({"status": "Metafrazo AI Backend Running"})


# ======================================================
# CHAT ENDPOINT
# ======================================================

@app.route("/chat", methods=["POST"])
def chat():

    global CURRENT_LANGUAGE
    global USER_SCORE
    global QUIZ_ACTIVE
    global QUIZ_CORRECT_OPTION
    global QUIZ_CORRECT_TEXT

    data_json = request.get_json(silent=True) or {}

    msg = normalize(data_json.get("message", ""))
    language = data_json.get("language")

    if not msg:
        return jsonify({"reply": "Please type something 😊"})

    # ---------------------------------------------------
    # LANGUAGE SELECTION
    # ---------------------------------------------------

    if language in LANGUAGES:
        CURRENT_LANGUAGE = language
    else:
        CURRENT_LANGUAGE = detect_language(msg)

    data = LANGUAGES.get(CURRENT_LANGUAGE, {})

    # ---------------------------------------------------
    # QUIZ ANSWER MODE
    # ---------------------------------------------------

    if QUIZ_ACTIVE:

        user_input = msg

        if user_input in ["a", "b", "c", "d"]:
            is_correct = user_input == QUIZ_CORRECT_OPTION
        else:
            is_correct = user_input == QUIZ_CORRECT_TEXT

        if is_correct:

            USER_SCORE += 5

            reply = f"✅ Correct!\n\n🪙 Score: {USER_SCORE}"

        else:

            reply = (
                f"❌ Wrong!\n"
                f"Correct answer: {QUIZ_CORRECT_OPTION.upper()}) {QUIZ_CORRECT_TEXT}\n\n"
                f"🪙 Score: {USER_SCORE}"
            )

        QUIZ_ACTIVE = False
        QUIZ_CORRECT_OPTION = None
        QUIZ_CORRECT_TEXT = None

        return jsonify({
            "reply": reply,
            "score": USER_SCORE
        })

    # ---------------------------------------------------
    # TEXT LANGUAGE SWITCH
    # ---------------------------------------------------

    if msg.startswith("learn "):

        lang = msg.replace("learn", "").strip()

        if lang in LANGUAGES:

            CURRENT_LANGUAGE = lang

            return jsonify({
                "reply": f"🌍 Language switched to {LANGUAGE_LABELS[lang]}"
            })

    # ---------------------------------------------------
    # QUIZ START
    # ---------------------------------------------------

    if "quiz" in msg:

        for key, value in data.get("quiz", {}).items():

            if smart_match(msg, key):

                matches = re.findall(r"([A-D])\)\s*(.*)", value)

                if not matches:
                    return jsonify({"reply": "Quiz format error."})

                correct_letter, correct_text = matches[-1]

                QUIZ_CORRECT_OPTION = correct_letter.lower()
                QUIZ_CORRECT_TEXT = correct_text.strip().lower()

                QUIZ_ACTIVE = True

                return jsonify({
                    "reply": f"📝 Quiz Started!\n\n{value}\n\nType A, B, C, D or full answer",
                    "score": USER_SCORE
                })

    # ---------------------------------------------------
    # LESSONS
    # ---------------------------------------------------

    result = search_category(data, "lessons", msg)

    if result:

        USER_SCORE += 2

        return jsonify({
            "reply": f"{result}\n\n🪙 Score: {USER_SCORE}",
            "score": USER_SCORE
        })

    # ---------------------------------------------------
    # PRACTICE
    # ---------------------------------------------------

    result = search_category(data, "practice", msg)

    if result:

        USER_SCORE += 3

        return jsonify({
            "reply": f"{result}\n\n🪙 Score: {USER_SCORE}",
            "score": USER_SCORE
        })

    # ---------------------------------------------------
    # OTHER CATEGORIES
    # ---------------------------------------------------

    for category in [
        "basics",
        "swar_faqs",
        "vyanjan_faqs",
        "barakhadi_faqs",
        "tenses",
        "numbers",
        "sentences",
        "hindi_grammar",
        "hindi_tenses"
    ]:

        result = search_category(data, category, msg)

        if result:
            return jsonify({"reply": result})

    # ---------------------------------------------------
    # SHORTCUTS
    # ---------------------------------------------------

    if "swar" in msg:

        result = search_category(data, "swar_faqs", "list swar")

        if result:
            return jsonify({"reply": result})

    if "vyanjan" in msg:

        result = search_category(data, "vyanjan_faqs", "list vyanjan")

        if result:
            return jsonify({"reply": result})

    if "barakhadi" in msg:

        result = search_category(data, "barakhadi_faqs", "what is barakhadi")

        if result:
            return jsonify({"reply": result})

    if "streak" in msg:

        return jsonify({
            "reply": f"🔥 Current streak: {USER_STREAK} day(s)"
        })

    # ---------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------

    return jsonify({
        "reply": (
            f"I'm currently teaching {LANGUAGE_LABELS[CURRENT_LANGUAGE]} 🌍\n\n"
            "Try:\n"
            "• teach noun\n"
            "• practice noun\n"
            "• quiz noun\n"
            "• help"
        )
    })


# ======================================================
# RUN SERVER
# ======================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)