import os
import sys

# Ensure modules can be imported correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from phase1_ingestion.ingestion import ingest_play_store_reviews
from phase2_theme_discovery.discovery import discover_themes
from phase3_weekly_note.generation import generate_weekly_pulse
from phase4_email_delivery.delivery import send_pulse_email

def main():
    print("=== Starting Weekly Review Pulse Pipeline ===")
    
    # Load keys
    groq_key = os.environ.get("GROQ_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not all([groq_key, gemini_key, sender, password]):
        print("Missing required environment variables. Ensure GROQ_API_KEY, GEMINI_API_KEY, GMAIL_ADDRESS, and GMAIL_APP_PASSWORD are set.")
        sys.exit(1)
        
    # We default the recipient to the sender email if one isn't provided
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)
    
    print("\n[Phase 1] Running Ingestion...")
    try:
        # Defaulting configuration for automated run: 8 weeks, 500 reviews
        df = ingest_play_store_reviews(max_reviews=500, weeks_lookback=8)
        if df.empty:
            print("No reviews found. Exiting.")
            sys.exit(0)
    except Exception as e:
        print(f"Ingestion failed: {e}")
        sys.exit(1)
    
    print(f"\n[Phase 2] Discovering and Classifying Themes for {len(df)} reviews...")
    try:
        themes_data = discover_themes(df, groq_key)
    except Exception as e:
        print(f"Theme Discovery failed: {e}")
        sys.exit(1)
    
    print("\n[Phase 3] Generating Weekly Pulse Note...")
    try:
        pulse_data = generate_weekly_pulse(themes_data, df, gemini_key)
        
        # Calculate Trend Data exactly like the FastAPI backend does
        import pandas as pd
        df["date"] = pd.to_datetime(df["date"])
        weekly_stats = df.set_index('date').resample('W').agg(
            avg_rating=('rating', 'mean'),
            review_count=('rating', 'count')
        ).dropna().reset_index()
        
        trend_data = []
        for i, (_, row) in enumerate(weekly_stats.iterrows(), start=1):
            end_date = row["date"]
            start_date = end_date - pd.Timedelta(days=6)
            trend_data.append({
                "weekLabel": f"Wk {i}: {start_date.strftime('%b %d')}-{end_date.strftime('%d')}",
                "avgRating": round(row["avg_rating"], 1),
                "count": int(row["review_count"])
            })
            
        pulse_data["trend_data"] = trend_data
        
    except Exception as e:
        print(f"Pulse Generation failed: {e}")
        sys.exit(1)
    
    print("\n[Phase 4] Drafting and Sending Email...")
    try:
        send_pulse_email(pulse_data, sender, password, recipient)
    except Exception as e:
        print(f"Email delivery failed: {e}")
        sys.exit(1)
    
    print("\n=== Pipeline Execution Completed Successfully ===")

if __name__ == "__main__":
    main()
