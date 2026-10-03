# 📅 DueSnap — AI Syllabus & Deadline Tracker

**DueSnap** is an intelligent vision-enabled academic and project companion that turns messy syllabus sheets, timetables, and assignment rubrics into clean, structured deadline agendas. 

Upload a photo of your course schedule, ask questions about weights and timelines, and instantly dispatch a complete, prioritized deadline digest directly to your **Telegram** inbox with a single click.

---

## 🌟 Features

- 📸 **Multimodal Gemini Vision**: Upload images of syllabi, exam timetables, assignment rubrics, or whiteboard schedules (`.jpg`, `.png`, `.webp`).
- 🤖 **Context-Aware Chat**: Inquire about assignment weighting, upcoming exams, or request a custom study roadmap.
- 📲 **Telegram Action Tool**: 1-click **"Send Digest to Telegram"** exports a formatted, chronological agenda straight to your Telegram account.
- 🛡️ **Edge-Case Handling**: Gracefully handles messy or low-resolution images without hallucinating dates.
- 🔒 **Zero Leaked Credentials**: Configured with strict `.gitignore` protection and `.streamlit/secrets.toml.example` templates.

---

## 🏗️ Architecture & Flow

```
[Student / User]
       │
       ▼ (1. Upload photo of Syllabus / Timetable)
[Streamlit Frontend] ──> [Gemini 3.1 Flash Vision + Chat]
       │                            │
       │ (2. Extract dates & query) │ (Structured breakdown)
       ▼                            ▼
[Chat Agenda Display] <─────────────┘
       │
       ▼ (3. Click "Send Digest to Telegram")
[python-telegram-bot] ──> [Telegram Bot API] ──> [User's Telegram Device 📲]
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))
- A Telegram account

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-link>
cd macrosnap

# Create and activate virtual environment
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Telegram Bot & Chat ID

1. Open Telegram, search for **`@BotFather`**, and send `/newbot`.
2. Follow the prompt to name your bot and copy the **Bot Token** (e.g. `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
3. Open your newly created bot in Telegram and tap **Start** (this allows the bot to message you).
4. Search for **`@userinfobot`** on Telegram and tap **Start** to view your numeric **Id** (e.g. `987654321`).

### 4. Configure Secrets

Create your local `.streamlit/secrets.toml` file (do NOT commit this file to GitHub):

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your-actual-gemini-api-key"
TELEGRAM_BOT_TOKEN = "your-actual-telegram-bot-token"
```

> 💡 A sample template is provided in [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example).

### 5. Run the Application

```bash
streamlit run app.py
```
*Or using the local venv path:*
```bash
.\venv\Scripts\python.exe -m streamlit run app.py
```

The app will launch at `http://localhost:8501`.

---

## 🌐 Deploy to Streamlit Community Cloud

1. Push your repository to GitHub (ensure `.streamlit/secrets.toml` is **not** committed).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **New app** and select your repository, branch (`main`), and main file path (`app.py`).
4. Under **Advanced Settings > Secrets**, paste your secrets:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
   ```
5. Click **Deploy!** 🚀

---

## 📁 Repository Structure

```
├── .streamlit/
│   ├── secrets.toml.example   # Safe public template for secrets
│   └── secrets.toml           # Local secrets (git-ignored)
├── app.py                     # Main Streamlit web application & Telegram integration
├── prompts.py                 # Structured system instructions & digest prompts
├── requirements.txt           # Project dependencies
├── .gitignore                 # Excludes secrets, venv, and cache files
└── README.md                  # Project documentation & setup instructions
```

---

## 📝 Submission Checklist

- [x] Functional vision extraction and conversational reasoning
- [x] Free action tool integration (Telegram Bot API)
- [x] Scoped system prompt with graceful degradation for messy images
- [x] `.streamlit/secrets.toml` safely ignored in `.gitignore`
- [x] Template `.streamlit/secrets.toml.example` provided
- [x] Complete setup guide & deployment instructions included
