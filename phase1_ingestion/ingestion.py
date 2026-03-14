import pandas as pd
import re
from datetime import datetime, timedelta
from google_play_scraper import reviews, Sort
from langdetect import detect

def remove_pii(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)
    text = re.sub(r'\b\d{10}\b', '[PHONE]', text)
    return text

def is_english(text: str) -> bool:
    try:
        return detect(text) == 'en'
    except:
        return False

def ingest_play_store_reviews(app_id="com.nextbillion.groww", max_reviews=200, weeks_lookback=8) -> pd.DataFrame:
    print(f"Fetching up to {max_reviews} reviews for '{app_id}'...")
    
    result, _ = reviews(
        app_id,
        lang="en",
        country="in",
        sort=Sort.NEWEST,
        count=max_reviews,
    )
    
    if not result:
        print("No reviews found.")
        return pd.DataFrame()

    # Extract only date, score, content (no title)
    df = pd.DataFrame(result)[["at", "score", "content"]]
    df.columns = ["date", "rating", "review"]
    
    # Filter by timeframe
    df["date"] = pd.to_datetime(df["date"])
    cutoff_date = datetime.now() - timedelta(weeks=weeks_lookback)
    df = df[df["date"] >= cutoff_date].copy()
    
    if df.empty:
        return df
        
    df["review"] = df["review"].fillna("").astype(str)
    
    # 1. PII Removal
    df["review"] = df["review"].apply(remove_pii)
    
    # 2. Filter word count >= 5 words
    df = df[df["review"].apply(lambda x: len(str(x).split()) >= 5)]
    
    # 3. Filter for English language only
    df = df[df["review"].apply(is_english)]
    
    df = df.reset_index(drop=True)
    print(f"Final dataset contains {len(df)} clean, English, >5 word reviews.")
    return df

if __name__ == "__main__":
    import os
    df_reviews = ingest_play_store_reviews(app_id="com.nextbillion.groww", max_reviews=200, weeks_lookback=8)
    
    if not df_reviews.empty:
        # Save to the root folder for visibility during testing, or inside the phase1 folder
        csv_filename = "cleaned_reviews_sample.csv"
        df_reviews.to_csv(f"../{csv_filename}", index=False)
        print(f"\nSaved sample to {csv_filename} for inspection.")
