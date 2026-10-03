import asyncio
import concurrent.futures
import streamlit as st
from google import genai
from google.genai import types
from telegram import Bot
from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.1-flash-lite"

st.set_page_config(
    page_title="DueSnap · Syllabus & Deadline Tracker",
    page_icon="📅",
    layout="centered",
)

# Load secrets with safe fallbacks
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")

if not GEMINI_API_KEY or "your-gemini-api-key" in GEMINI_API_KEY:
    st.error("⚠️ GEMINI_API_KEY is missing or invalid in `.streamlit/secrets.toml`.")
    st.stop()


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def send_telegram(chat_id: str, text: str):
    """Sends a formatted message to the user's Telegram via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or "your-telegram-bot-token" in TELEGRAM_BOT_TOKEN:
        return False, (
            "Telegram Bot Token not configured in `.streamlit/secrets.toml`. "
            "Please create a bot via @BotFather and add your token."
        )

    clean_chat_id = chat_id.strip()

    def _sync_send(content, parse_mode=None):
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        return asyncio.run(
            bot.send_message(
                chat_id=clean_chat_id,
                text=content,
                parse_mode=parse_mode,
            )
        )

    # Execute in a clean thread to avoid conflict with running asyncio event loops
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        try:
            # Try Markdown formatted send first
            future = pool.submit(_sync_send, text, "Markdown")
            msg = future.result(timeout=15)
            return True, f"Message ID: {msg.message_id}"
        except Exception:
            # Fallback to plain-text if Markdown has unescaped characters
            try:
                future = pool.submit(_sync_send, text, None)
                msg = future.result(timeout=15)
                return True, f"Message ID: {msg.message_id}"
            except Exception as final_error:
                error_msg = str(final_error)
                if "Chat not found" in error_msg:
                    return False, (
                        "Chat not found. Please open your bot in Telegram and tap "
                        "'START' before requesting a message."
                    )
                return False, error_msg


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.markdown(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    # Ensure current chat uses active MODEL_NAME
    if hasattr(st.session_state, "chat") and getattr(st.session_state.chat, "_model", None) != MODEL_NAME:
        st.session_state.chat._model = MODEL_NAME

    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        # Fallback handling for temporary demand spikes (503 UNAVAILABLE)
        if "503" in str(error) and getattr(st.session_state.chat, "_model", None) != "gemini-3.1-flash-lite":
            try:
                st.session_state.chat._model = "gemini-3.1-flash-lite"
                return st.session_state.chat.send_message(parts).text
            except Exception as fallback_err:
                return f"Sorry, something went wrong: {fallback_err}"
        return f"Sorry, something went wrong: {error}"


# Step 1: Onboarding
if "onboarded" not in st.session_state:
    st.title("📅 DueSnap")
    st.caption("Snap your syllabus, timetable, or assignment sheet. Extract deadlines. Text your digest to Telegram.")

    with st.form("onboarding_form"):
        name = st.text_input("Your Name", placeholder="e.g. Alex")
        telegram_chat_id = st.text_input(
            "Telegram Chat ID",
            placeholder="e.g. 123456789",
            help="Your numeric Telegram Chat ID where DueSnap will send your deadline digest.",
        )

        with st.expander("ℹ️ How to get your Telegram Chat ID (takes 30 seconds)"):
            st.markdown(
                """
                1. Open Telegram and search for **`@userinfobot`** (or `@raw_data_bot`).
                2. Tap **Start** or send any message. It will reply with your numeric **Id** (e.g., `987654321`).
                3. Paste that ID above.
                4. **Important**: Also make sure to open your configured bot on Telegram and tap **Start** once so it has permission to message you!
                """
            )

        submitted = st.form_submit_button("Start Tracking Deadlines 🚀", use_container_width=True)
        if submitted:
            if not name.strip() or not telegram_chat_id.strip():
                st.warning("Please fill in both your name and Telegram Chat ID.")
            else:
                st.session_state.name = name.strip()
                st.session_state.telegram_chat_id = telegram_chat_id.strip()
                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                )
                st.session_state.messages = []
                st.session_state.onboarded = True
                st.rerun()
    st.stop()


# Step 2: Main Interface
# Sidebar for user context and session control
with st.sidebar:
    st.title("📅 DueSnap")
    user_name = st.session_state.get("name", "Student")
    chat_id = st.session_state.get("telegram_chat_id", "Not set")
    st.markdown(f"**Student:** {user_name}")
    st.markdown(f"**Telegram ID:** `{chat_id}`")
    st.divider()

    st.markdown("### 💡 Quick Prompts")
    st.caption("Click to ask about your uploaded syllabus:")
    if st.button("🗓️ What is due first?", use_container_width=True):
        st.session_state.prefill_prompt = "What is due first according to the schedule?"
    if st.button("⚖️ What has the highest weight?", use_container_width=True):
        st.session_state.prefill_prompt = "Which assignment or exam carries the highest percentage or grade weight?"
    if st.button("📝 Create a study roadmap", use_container_width=True):
        st.session_state.prefill_prompt = "Create a structured preparation checklist and study roadmap for the upcoming deadlines."

    st.divider()
    if st.button("🔄 Reset / New Syllabus", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Top Header with Action Trigger
header_col, action_col = st.columns([5, 3], vertical_alignment="center")
with header_col:
    st.title("📅 DueSnap")
    st.caption("Snap syllabus, course timetables, or assignment sheets to track every deadline.")

with action_col:
    has_content = len(st.session_state.messages) > 1
    send_clicked = st.button(
        "📤 Send Digest to Telegram",
        disabled=not has_content,
        use_container_width=True,
        help="Analyzes your conversation and sends a structured agenda to your Telegram.",
    )

if send_clicked:
    with st.spinner("Generating your structured deadline digest..."):
        digest = ask_gemini([SUMMARY_REQUEST_PROMPT])
        success, info = send_telegram(st.session_state.telegram_chat_id, digest)
        if success:
            st.success("✅ Digest sent successfully! Check your Telegram 📲")
            with st.expander("👀 Preview Sent Digest"):
                st.markdown(digest)
        else:
            st.error(f"❌ Failed to send to Telegram: {info}")
            st.info(
                "💡 Tip: Ensure your `TELEGRAM_BOT_TOKEN` is configured in `.streamlit/secrets.toml` "
                "and you have pressed **Start** in your bot chat on Telegram."
            )

# Render Chat History
if not st.session_state.messages:
    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.get("name", "Student")),
    )
else:
    for message in st.session_state.messages:
        render_message(message)

# Handle prefill prompts from sidebar
prefilled_text = st.session_state.pop("prefill_prompt", None)

user_input = st.chat_input(
    "Ask a question, or attach a photo of your syllabus / timetable...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"],
)

active_input_text = None
active_input_photo = None

if user_input:
    active_input_text = user_input.text
    active_input_photo = user_input.files[0] if user_input.files else None
elif prefilled_text:
    active_input_text = prefilled_text

if active_input_text or active_input_photo:
    parts = []
    if active_input_photo is not None:
        photo_bytes = active_input_photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=active_input_photo.type))

    if active_input_text:
        add_message("user", "text", active_input_text)
        parts.append(active_input_text)
    elif active_input_photo is not None:
        default_query = (
            "Analyze this syllabus/schedule photo. Extract all assignments, exam dates, "
            "deadlines, weights, and key submission details into a structured breakdown."
        )
        parts.append(default_query)

    with st.spinner("Extracting dates & deliverables..."):
        answer = ask_gemini(parts)
        add_message("assistant", "text", answer)
