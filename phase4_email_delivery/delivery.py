import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

def generate_sparkline(trend_data: list) -> str:
    """Converts a list of dicts with 'avgRating' into an ASCII sparkline string."""
    if not trend_data:
        return ""
    
    # 1=low, 5=high. We map to 8 unicode blocks:  ▂▃▄▅▆▇█
    blocks = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    
    sparkline_str = ""
    for point in trend_data:
        # Scale the rating (1.0 - 5.0) to an index (0 - 8)
        rating = point.get('avgRating', 1)
        # Normalize: (rating - 1) / (5 - 1) gives us a 0 to 1 float
        normalized = max(0, min(1, (rating - 1) / 4))
        idx = int(normalized * 8)
        sparkline_str += blocks[idx]
        
    return sparkline_str

def send_pulse_email(pulse: dict, sender_email: str, app_password: str, recipient_email: str):
    """
    Converts the Weekly Pulse JSON into a styled HTML email and sends it via SMTP.
    """
    
    # 1. Generate HTML Body
    themes_html = "".join([
        f"<p><strong>{t['rank']}. {t['name']}</strong> &nbsp; "
        f"{'🔴' if t['sentiment']=='negative' else '🟢' if t['sentiment']=='positive' else '🟡'} "
        f"{t['review_count']} mentions<br>"
        f"<span style='color:#666'>{t['summary']}</span></p>" 
        for t in pulse.get('top_3_themes', [])
    ])
    
    quotes_html = "".join([
        f"<blockquote style='border-left:3px solid #f4c542; padding-left:12px; color:#555; font-style:italic;'>"
        f"\"{q}\"</blockquote>" 
        for q in pulse.get('top_3_quotes', [])
    ])
    
    actions_html = "".join([
        f"<li style='margin-bottom:8px'>{a}</li>" 
        for a in pulse.get('top_3_actions', [])
    ])
    
    # Generate Trend Line HTML block if trend data exists
    trend_html = ""
    if 'trend_data' in pulse and pulse['trend_data']:
        sparkline = generate_sparkline(pulse['trend_data'])
        last_week = pulse['trend_data'][-1]['weekLabel']
        trend_html = f"""
        <div style="margin-top: 20px; padding: 15px; background-color: #f0fdf4; border-left: 4px solid #00d09c; border-radius: 4px;">
            <p style="margin:0; font-size: 14px; color: #065f46;">
                <strong>Weekly Trend ({pulse['trend_data'][0]['weekLabel']} to {last_week})</strong>
            </p>
            <p style="margin: 5px 0 0 0; font-size: 24px; color: #00d09c; letter-spacing: 2px;">
                {sparkline}
            </p>
        </div>
        """

    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
        <h1 style="color: #00d09c; font-size: 24px; border-bottom: 2px solid #00d09c; padding-bottom: 10px;">{pulse.get('title', 'Weekly Review Pulse')}</h1>
        
        <p style="color: #666; font-size: 14px; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
            <strong>Period:</strong> {pulse.get('date_range', 'N/A')} &nbsp;|&nbsp;
            <strong>Analyzed:</strong> {pulse.get('total_reviews', 0)} reviews &nbsp;|&nbsp;
            <strong>Avg Rating:</strong> {pulse.get('avg_rating', 0)}★ &nbsp;|&nbsp;
            <strong>Sentiment:</strong> {str(pulse.get('overall_sentiment', '')).capitalize()}
        </p>
        
        {trend_html}

        <h2 style="color: #00d09c; font-size: 18px; margin-top: 25px;">🏷️ Top Themes</h2>
        {themes_html}

        <hr style="border: 0; height: 1px; background: #eee; margin: 25px 0;">
        <h2 style="color: #00d09c; font-size: 18px;">💬 User Voices</h2>
        {quotes_html}

        <hr style="border: 0; height: 1px; background: #eee; margin: 25px 0;">
        <h2 style="color: #00d09c; font-size: 18px;">⚡ Top Action Items</h2>
        <ol style="padding-left: 20px;">
            {actions_html}
        </ol>

        <hr style="border: 0; height: 1px; background: #eee; margin: 30px 0 10px 0;">
        <p style="color: #999; font-size: 11px; text-align: center;">
            Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')} · AI PM Pulse Generator
        </p>
    </body>
    </html>
    """

    # 2. Configure Email Headers
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Groww Weekly Review Pulse — {datetime.now().strftime('%d %b %Y')}"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    
    # 3. Attach HTML content
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # 4. Send via SMTP (Defaulting to Gmail)
    print(f"Connecting to SMTP server to send email to {recipient_email}...")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise e

if __name__ == "__main__":
    # Test execution
    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL", sender) # Default to sending to self if not specified
    
    if not sender or not password:
        print("Error: GMAIL_ADDRESS or GMAIL_APP_PASSWORD environment variables are not set.")
        print("Please run:")
        print("export GMAIL_ADDRESS='your-email@gmail.com'")
        print("export GMAIL_APP_PASSWORD='your-app-password'")
    else:
        try:
            # Load the pulse generated in Phase 3
            with open("../phase3_weekly_note/weekly_pulse_sample.json", "r") as f:
                pulse_data = json.load(f)
                
            print(f"Loaded generated pulse for {pulse_data.get('date_range')}.")
            send_pulse_email(pulse_data, sender, password, recipient)
            
        except FileNotFoundError:
            print("Error: weekly_pulse_sample.json not found.")
            print("Please run Phase 3 generation first.")
