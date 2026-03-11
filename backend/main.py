from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pandas as pd
import io
import os
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tempfile
import shutil
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import re
from typing import Optional

app = FastAPI(title="Sales Insight Automator API", version="1.0.0")

# Security
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.vercel.app"],  # Update with actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

client = Groq(api_key=GROQ_API_KEY)

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def process_csv_data(file_content: bytes) -> str:
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        # Basic data validation
        required_columns = ['Date', 'Product_Category', 'Region', 'Units_Sold', 'Unit_Price', 'Revenue', 'Status']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("CSV must contain required columns: Date, Product_Category, Region, Units_Sold, Unit_Price, Revenue, Status")
        
        # Convert to string for AI processing
        data_summary = df.to_string(index=False)
        return data_summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

def generate_ai_summary(data: str) -> str:
    prompt = f"""
    Analyze the following sales data and generate a professional executive summary. 
    Focus on key insights, trends, and recommendations. Keep it concise but comprehensive.
    
    Sales Data:
    {data}
    
    Please provide:
    1. Overall performance summary
    2. Key trends by category and region
    3. Revenue analysis
    4. Recommendations for improvement
    """
    
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, to_email, text)
        server.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

@app.post("/upload")
@limiter.limit("5/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    email: str = None
):
    # Validate email
    if not email or not validate_email(email):
        raise HTTPException(status_code=400, detail="Valid email address is required")
    
    # Validate file type
    if file.filename.split('.')[-1].lower() not in ['csv', 'xlsx']:
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are allowed")
    
    # Validate file size (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    try:
        # Process data
        data_summary = process_csv_data(file_content)
        
        # Generate AI summary
        ai_summary = generate_ai_summary(data_summary)
        
        # Send email
        subject = "Sales Insight Summary - Q1 2026"
        send_email(email, subject, ai_summary)
        
        return {"message": "Summary generated and sent successfully", "summary": ai_summary}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)