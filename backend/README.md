# Sales Insight Automator - Backend

FastAPI backend service for processing sales data and generating AI summaries.

## Features

- File upload with validation
- AI-powered summary generation using Groq
- Email delivery via SMTP
- Rate limiting and security measures
- Swagger documentation

## Security Measures

- Rate limiting (5 requests/minute per IP)
- File type and size validation
- Input sanitization
- CORS protection
- Environment variable management

## API Endpoints

- `POST /upload`: Upload CSV/XLSX file and email address
- `GET /health`: Health check

## Environment Variables

Required:
- `GROQ_API_KEY`: Your Groq API key
- `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)
- `SMTP_USERNAME`: SMTP username
- `SMTP_PASSWORD`: SMTP password
- `FROM_EMAIL`: Sender email address