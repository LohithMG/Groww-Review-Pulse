# Architecture Document: Actions on Reviews for "Groww"

## 1. Project Overview
**Goal:** Automatically turn recent App Store and Play Store reviews for the **Groww** application into a concise, actionable, one-page weekly pulse and send it via email.
**Target Audience:** Product / Growth Teams, Support Teams, Leadership.
**Core AI Stack:** Groq (for fast theme discovery) and Gemini (for generation).

### Key Constraints
- Use public review exports only (no scraping behind logins).
- Limit themes to a maximum of 5.
- Keep the final note scannable and under 250 words.
- Strictly **NO PII** (Personally Identifiable Information like usernames, emails, or user IDs) in artifacts.

---

## 2. Phase-Wise Architecture

### Phase 1: Review Ingestion and Cleaning
**Objective:** Fetch, filter, and normalize review data from public stores.
- **Data Sources:** 
  - Google Play Store (`google-play-scraper` or public API exports).
  - Apple App Store (`app-store-scraper` or RSS feeds).
- **Timeframe:** Retrieve reviews from the past 8 to 12 weeks.
- **Data Points Collected:** Rating, Title, Text, Date. 
- **PII Stripping:** Explicitly drop author names, IDs, and any obvious PII from the review text using regex/heuristics before saving.
- **Cleaning:** Remove empty reviews, non-English reviews (optional), and extremely short unhelpful text (e.g., "good").
- **Storage:** Store cleaned texts in a lightweight local database (e.g., SQLite or Pandas DataFrame / CSV for simple state management).

### Phase 2: Theme Discovery and Classification
**Objective:** Identify common patterns and categorize reviews.
- **LLM Provider:** **Groq** (chosen for high-speed inference).
- **Theme Generation:**
  - Inject a sample/batch of cleaned reviews into a Groq prompt.
  - Instruct the model to identify the top recurring themes strictly capped at 3 to 5 themes.
- **Classification / Grouping:**
  - Route the remaining reviews through Groq to classify them into the identified themes.
  - Aggregate reviews by theme to prepare for the summarization phase.

### Phase 3: Weekly Note Generation
**Objective:** Synthesize the categorized data into a scannable one-pager.
- **LLM Provider:** **Gemini**.
- **Prompt Strategy:** Pass the categorized themes and their most relevant reviews to Gemini with strict output formatting rules.
- **Output Requirements:**
  - **Top 3 Themes:** A brief bulleted summary of the most prominent issues/praises.
  - **Real User Quotes:** 3 powerful, representative (and fully anonymized) quotes.
  - **Action Ideas:** 3 concrete recommendations for Product, Growth, or Support teams.
  - **Length:** Maximum 250 words.

### Phase 4: Email Delivery
**Objective:** Automatically draft and distribute the weekly note.
- **Email Gateway:** SMTP (e.g., Gmail App Passwords), SendGrid, or Resend.
- **Formatting:** Convert the Gemini markdown output into clean HTML.
- **Execution:** Send the drafted email to a configured alias or the user.

### Phase 5: User Interface (UI) & Backend Orchestration
**Objective:** Provide a robust, enterprise-grade architecture to trigger the pipeline instead of relying on CLI scripts.
- **Frameworks:**
  - **Backend:** FastAPI (Python) server to securely orchestrate the LLM pipeline and expose REST API endpoints.
  - **Frontend:** React (Vite) + Tailwind CSS providing a premium "Dark Fintech" aesthetic layout with Recharts for dynamic visualizations.
- **Features:**
  - A dashboard to configure ingestion settings (weeks, max reviews).
  - An "Analyze Latest Reviews" trigger button for Phases 1-3 with map-reduce processing.
  - A dynamic visualization showing the weekly average rating trend.
  - A preview pane to read the generated note and Top 3 Themes.
  - A "Send Pulse Report" trigger button to execute Phase 4 with ASCII sparklines.

---

## 3. Tech Stack Summary
- **Backend API / Scripting:** Python, FastAPI, Uvicorn, Pandas
- **Data Scraping:** `google-play-scraper`, `app-store-scraper`
- **AI Models:** 
  - Groq API (Theme Discovery & Classification via Map-Reduce logic)
  - Google Gemini API (Content Generation)
- **UI (Frontend):** React.js (Vite), Tailwind CSS, Recharts, Lucide Icons
- **Delivery:** Python `smtplib` / HTML Email with generated ASCII Sparklines
