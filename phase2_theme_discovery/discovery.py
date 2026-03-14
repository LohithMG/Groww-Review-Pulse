import pandas as pd
import json
import re
import time
from groq import Groq
import os

def extract_themes_from_batch(reviews_batch: list, client: Groq) -> dict:
    """Helper step -> MAP: Extracts themes from a single small batch of reviews."""
    reviews_text = "\n".join([f"[{r['rating']}★] {r['review']}" for r in reviews_batch])
    prompt = f"""You are a top-tier product analyst. Analyze these recent app reviews.
Identify the recurring patterns and problems.
Return ONLY valid JSON, no markdown formatting out of bounds, no code fences.

Reviews:
{reviews_text}

Return exactly in this JSON format:
{{
  "themes": [
    {{
      "name": "Theme Name (e.g., UI/UX, Performance, Customer Support)",
      "description": "One line summarizing the issue or praise",
      "review_count": 45,
      "sentiment": "negative",
      "top_quotes": ["Short quote under 20 words", "Another short quote"]
    }}
  ]
}}

STRICT RULES:
- Maximum 5 themes.
- No usernames, emails, or phone numbers in quotes.
- `sentiment` field MUST be exactly one of: "positive", "negative", or "mixed".
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2000,
        )
        raw_output = response.choices[0].message.content.strip()
        if not raw_output:
            print("Batch extraction returned empty content.")
            return {"themes": []}
            
        # Clean potential markdown (though json_object should prevent it)
        raw_output = re.sub(r'^```[a-zA-Z]*\n', '', raw_output)
        raw_output = re.sub(r'\n```$', '', raw_output)
        return json.loads(raw_output.strip())
    except Exception as e:
        print(f"Batch extraction failed: {e}")
        return {"themes": []}

def reduce_themes(all_sub_themes: list, client: Groq) -> dict:
    """Helper step -> REDUCE: Takes many sub-themes from batches and merges them into 5 max."""
    themes_text = json.dumps(all_sub_themes, indent=2)
    prompt = f"""You are a Lead Product Analyst. 
I have run batch analysis on thousands of reviews and extracted these sub-themes from the batches.
Merge, deduplicate, and consolidate these into a final Top 5 Major Themes report.

Sub-themes across batches:
{themes_text}

Return exactly in this JSON format:
{{
  "themes": [
    {{
      "name": "Consolidated Theme Name",
      "description": "One line summarizing the consolidated issue",
      "review_count": 120, 
      "sentiment": "negative",
      "top_quotes": ["Best quote 1", "Best quote 2"]
    }}
  ]
}}

STRICT RULES:
- Maximum 5 themes total.
- Sum up the review_counts for merged themes.
- Keep the very best quotes.
- `sentiment` must be exactly one of: "positive", "negative", or "mixed".
- ONLY valid parseable JSON. No backticks. No markdown.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000,
        )
        raw_output = response.choices[0].message.content.strip()
        if not raw_output:
            raise ValueError("Reduce phase returned empty content from LLM.")
            
        raw_output = re.sub(r'^```[a-zA-Z]*\n', '', raw_output)
        raw_output = re.sub(r'\n```$', '', raw_output)
        return json.loads(raw_output.strip())
    except json.JSONDecodeError as e:
        print(f"Theme reduction JSON decode failed. Raw output:\n{raw_output}")
        raise ValueError("Failed to parse reduction output as JSON.") from e
    except Exception as e:
        print(f"Theme reduction failed: {e}")
        raise e

def discover_themes(df: pd.DataFrame, api_key: str, batch_size: int = 150) -> dict:
    """
    Uses Groq (Llama 3) to analyze a batch of reviews and discover up to 5 main themes.
    Implements Map-Reduce batching to handle unlimited reviews without hitting context limits.
    """
    if df.empty:
        return {"themes": []}
        
    client = Groq(api_key=api_key)
    
    records = df[["rating", "review"]].to_dict(orient="records")
    total_reviews = len(records)
    
    # 1. Map Phase: Chunk and extract
    all_sub_themes = []
    
    print(f"Batching {total_reviews} reviews into chunks of {batch_size}...")
    for i in range(0, total_reviews, batch_size):
        batch = records[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}...")
        batch_result = extract_themes_from_batch(batch, client)
        all_sub_themes.extend(batch_result.get("themes", []))
        
        # Add a delay between batches to respect Groq rate limits
        if (i + batch_size) < total_reviews:
            time.sleep(1.5)
        
    if not all_sub_themes:
        return {"themes": []}
        
    # 2. Reduce Phase: If we had more than one batch, reduce them down to 5.
    if total_reviews > batch_size:
        print("Reducing sub-themes into final top 5...")
        final_themes = reduce_themes(all_sub_themes, client)
        print(f"Successfully synthesized {len(final_themes.get('themes', []))} major themes.")
        return final_themes
    else:
        # If it all fit in one batch anyway, just return the map result
        print(f"Successfully extracted {len(all_sub_themes)} themes from single batch.")
        return {"themes": all_sub_themes[:5]}

if __name__ == "__main__":
    # Test execution
    # Ensure you have set the GROQ_API_KEY environment variable.
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        print("Please run: export GROQ_API_KEY='your-key-here'")
    else:
        # Load the sample data from Phase 1
        try:
            df_reviews = pd.read_csv("../cleaned_reviews_sample.csv")
            print(f"Loaded {len(df_reviews)} reviews for theme extraction.")
            
            themes_data = discover_themes(df_reviews, api_key)
            
            print("\n--- Extracted Themes ---")
            print(json.dumps(themes_data, indent=2))
            
            # Save output for Phase 3
            with open("themes_output_sample.json", "w") as f:
                json.dump(themes_data, f, indent=2)
            print("\nSaved extracted themes to themes_output_sample.json")
            
        except FileNotFoundError:
            print("Error: cleaned_reviews_sample.csv not found in the root directory.")
            print("Please run Phase 1 ingestion first.")
