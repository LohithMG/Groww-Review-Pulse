import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path so we can import our existing modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from phase1_ingestion.ingestion import ingest_play_store_reviews
from phase2_theme_discovery.discovery import discover_themes
from phase3_weekly_note.generation import generate_weekly_pulse
from phase4_email_delivery.delivery import send_pulse_email

# Load environment variables (API keys, email credentials)
load_dotenv()

app = FastAPI(
    title="Groww Review Pulse API",
    description="Backend API for ingesting, analyzing, and synthesizing app store reviews.",
    version="1.0.0"
)

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to the React app URL (e.g. http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Input Validation ---

class AnalyzeRequest(BaseModel):
    weeks: int = 8
    max_reviews: int = 500
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

class EmailRequest(BaseModel):
    recipient_email: EmailStr
    pulse_data: dict # The JSON output from the analyze endpoint
    sender_email: Optional[str] = None
    app_password: Optional[str] = None

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Groww Review Pulse Engine API is running"}

@app.post("/api/v1/analyze")
def analyze_reviews(request: AnalyzeRequest):
    """
    Executes Phases 1, 2, and 3: 
    Ingests reviews, discovers themes via Groq, and generates a pulse via Gemini.
    """
    # 1. Resolve API Keys (from request overlay, else fallback to .env)
    groq_key = request.groq_api_key or os.environ.get("GROQ_API_KEY")
    gemini_key = request.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    
    if not groq_key or not gemini_key:
        raise HTTPException(status_code=401, detail="Missing Groq or Gemini API Keys in both request and .env file.")

    # 2. Phase 1: Ingestion
    print(f"[API] Starting Phase 1: Fetching up to {request.max_reviews} reviews...")
    try:
        df = ingest_play_store_reviews(max_reviews=request.max_reviews, weeks_lookback=request.weeks)
        if df.empty:
            raise HTTPException(status_code=404, detail="No reviews found for the specified timeframe.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phase 1 Ingestion Failed: {str(e)}")

    # 3. Phase 2: Theme Discovery
    print(f"[API] Starting Phase 2: Discovering themes across {len(df)} clean reviews...")
    try:
        themes_data = discover_themes(df, groq_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phase 2 Theme Discovery Failed: {str(e)}")

    # 4. Phase 3: Weekly Pulse Generation
    print("[API] Starting Phase 3: Synthesizing final pulse...")
    try:
        pulse_data = generate_weekly_pulse(themes_data, df, gemini_key)
        
        # 5. Extract Weekly Trend Chart Data
        # Ensure the date column is datetime
        df["date"] = pd.to_datetime(df["date"])
        # Set date as index and group by week (W-MON format groups by Week ending on Monday)
        weekly_stats = df.set_index('date').resample('W').agg(
            avg_rating=('rating', 'mean'),
            review_count=('rating', 'count')
        ).dropna().reset_index()
        
        # Format for React Recharts
        trend_data = []
        for i, (_, row) in enumerate(weekly_stats.iterrows(), start=1):
            # 'W' resamples to the end of the week (Sunday). The start of that week (Monday) is 6 days prior.
            end_date = row["date"]
            start_date = end_date - pd.Timedelta(days=6)
            trend_data.append({
                "weekLabel": f"Wk {i}: {start_date.strftime('%b %d')}-{end_date.strftime('%d')}",
                "avgRating": round(row["avg_rating"], 1),
                "count": int(row["review_count"])
            })
            
        pulse_data["trend_data"] = trend_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phase 3 Pulse Generation Failed: {str(e)}")

    print("[API] Pipeline complete!")
    return {
        "status": "success",
        "message": "Analysis completed successfully.",
        "data": pulse_data
    }

@app.post("/api/v1/email")
def send_email(request: EmailRequest):
    """
    Executes Phase 4: Emails the generated pulse report.
    """
    sender = request.sender_email or os.environ.get("GMAIL_ADDRESS")
    password = request.app_password or os.environ.get("GMAIL_APP_PASSWORD")

    if not sender or not password:
        raise HTTPException(status_code=401, detail="Missing Gmail credentials in both request and .env file.")

    print(f"[API] Starting Phase 4: Sending email to {request.recipient_email}...")
    try:
        send_pulse_email(
            pulse=request.pulse_data,
            sender_email=sender,
            app_password=password,
            recipient_email=request.recipient_email
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phase 4 Email Delivery Failed: {str(e)}")
        
    return {"status": "success", "message": f"Email successfully delivered to {request.recipient_email}"}

if __name__ == "__main__":
    print("Starting Groww API Server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
