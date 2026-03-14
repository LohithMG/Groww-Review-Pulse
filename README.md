# Groww Review Pulse Engine

Automatically turn App Store and Google Play Store reviews into a concise, actionable, one-page weekly pulse and send it via email. Built with FastAPI, React, Groq, and Gemini.

## 🚀 Features

*   **Review Ingestion:** Automatically fetches the latest reviews from public app stores for the specified timeframe.
*   **Theme Discovery (via Groq):** Rapidly analyzes reviews to identify the top 3-5 recurring themes.
*   **Pulse Synthesis (via Gemini):** Generates a succinct, actionable report including theme summaries, real user quotes, and concrete PM action items.
*   **Delivery:** Can securely email the final report.
*   **Dark Fintech UI:** A sleek, reactive dashboard to manually trigger runs, view historical rating trends, and preview the latest report.

## 🛠️ Architecture

The app is split into a robust Python backend and a modern React frontend:

**Backend (`/backend`)**
*   **Framework:** FastAPI (Python 3.9+)
*   **LLMs:**
    *   `Groq` for high-speed theme extraction and map-reduce processing.
    *   `Google Gemini` for final structural synthesis and content formatting.
*   **Core Logic:** The logic is broken down into modular phases (`phase1_ingestion`, `phase2_theme_discovery`, `phase3_weekly_note`, `phase4_email_delivery`).

**Frontend (`/frontend`)**
*   **Framework:** React 19 (Vite)
*   **Styling:** Tailwind CSS (Dark theme with custom glassmorphism components)
*   **Icons & Charts:** Lucide React & Recharts

For more details on the design, see [`architecture.md`](./architecture.md).

## 💻 Getting Started (Local Development)

### 1. Prerequisites
*   Python 3.9+ 
*   Node.js (for the frontend)
*   API Keys for **Groq**, **Google Gemini**, and an SMTP email account (like a Gmail App Password).

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY="your_groq_key"
GEMINI_API_KEY="your_gemini_key"
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your_app_password"
```

### 3. Start the Backend
```bash
pip install -r requirements.txt
cd backend
python -m uvicorn main:app --reload
```
The API will run at `http://localhost:8000`.

### 4. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
The UI will run at `http://localhost:5173`.

## 📦 Automation

While the UI allows manual triggering, the pipeline is designed to be fully automated. You can write a standalone Python script to call the phases sequentially and schedule it using a cron job or **GitHub Actions**.

## 🔒 Security Note
*   The system strips obvious personally identifiable information (PII) before LLM processing.
*   Do not commit your `.env` file or expose your API keys.
