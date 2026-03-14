import json
import re
import pandas as pd
from google import genai
import os

def generate_weekly_pulse(themes_data: dict, df: pd.DataFrame, api_key: str) -> dict:
    """
    Uses Gemini to synthesize the extracted themes and raw statistics into a 
    scannable weekly pulse note (max 250 words total).
    """
    
    client = genai.Client(api_key=api_key)

    # Calculate basic stats
    avg_rating = round(df["rating"].mean(), 1) if not df.empty else 0
    total = len(df)
    if not df.empty:
        date_range = f"{df['date'].min().strftime('%d %b')} – {df['date'].max().strftime('%d %b %Y')}"
    else:
        date_range = "Unknown"

    prompt = f"""You are a PM writing a weekly app review pulse note for leadership and the team.

Data Context:
- Period: {date_range}
- Total English reviews analyzed: {total}
- Average rating in this sample: {avg_rating}★
- Themes discovered by our data engine:
{json.dumps(themes_data.get('themes', []), indent=2)}

Generate a scannable, highly impactful weekly pulse note.
Return ONLY valid JSON, no markdown formatting out of bounds, no code fences.

Your JSON MUST strictly match this exact schema:
{{
  "title": "Groww Weekly Review Pulse",
  "date_range": "{date_range}",
  "total_reviews": {total},
  "avg_rating": {avg_rating},
  "overall_sentiment": "mixed", 
  "top_3_themes": [
    {{
      "rank": 1,
      "name": "Exact Theme Name",
      "review_count": 45,
      "sentiment": "negative",
      "summary": "One sharp sentence summarizing this theme."
    }}
  ],
  "top_3_quotes": [
    "Most impactful, fully anonymized quote 1",
    "Most impactful, fully anonymized quote 2",
    "Most impactful, fully anonymized quote 3"
  ],
  "top_3_actions": [
    "Specific, immediate action recommendation 1 for Product/Growth teams",
    "Specific, immediate action recommendation 2",
    "Specific, immediate action recommendation 3"
  ],
  "word_count": 200
}}

STRICT RULES:
- Exactly 3 themes, 3 quotes, and 3 actions.
- The entire content generated across all string fields MUST visually read as under 250 words.
- NO usernames, passwords, emails, or PII.
- Actions MUST be extremely specific and relevant to the themes provided (e.g., if login fails, suggest fixing auth flow).
"""

    print("Sending prompt to Gemini API...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        raw_output = response.text.strip()
        
        # Guard against markdown code blocks
        raw_output = re.sub(r'^```json\s*', '', raw_output)
        raw_output = re.sub(r'^```\s*', '', raw_output)
        raw_output = re.sub(r'\s*```$', '', raw_output)
        
        parsed_json = json.loads(raw_output.strip())
        print("Successfully generated final Weekly Pulse Note via Gemini.")
        return parsed_json
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from Gemini. Raw output was:\n{raw_output}")
        raise e
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        raise e


if __name__ == "__main__":
    # Test execution
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Please run: export GEMINI_API_KEY='your-key-here'")
    else:
        try:
            # 1. Load original dataframe for dates & stats
            df_reviews = pd.read_csv("../cleaned_reviews_sample.csv")
            # Need to cast date back to datetime
            df_reviews["date"] = pd.to_datetime(df_reviews["date"])
            
            # 2. Load the themes discovered in Phase 2
            with open("../phase2_theme_discovery/themes_output_sample.json", "r") as f:
                themes_data = json.load(f)
                
            print(f"Loaded {len(df_reviews)} raw reviews and their themes. Synthesizing...")
            
            # 3. Generate Pulse
            pulse_data = generate_weekly_pulse(themes_data, df_reviews, api_key)
            
            print("\n--- Final Weekly Pulse (JSON) ---")
            print(json.dumps(pulse_data, indent=2))
            
            # 4. Save
            with open("weekly_pulse_sample.json", "w") as f:
                json.dump(pulse_data, f, indent=2)
            print("\nSaved pulse to weekly_pulse_sample.json")
            
        except FileNotFoundError as e:
            print(f"Error missing file for testing: {e}")
            print("Please ensure Phase 1 and Phase 2 outputs exist.")
