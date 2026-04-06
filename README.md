# Mini SIEM Security Onion Dashboard

Simple Flask-based dashboard for monitoring Security Onion Elasticsearch data.

## Features
- Total events in last 24h
- Critical / High / Medium counts
- Timeline chart
- Top source IPs
- Recent alerts table

## Setup
1. Create virtual environment
2. Install dependencies
3. Copy `.env.example` to `.env`
4. Fill in your Security Onion credentials
5. Run app

## Run
```bash
python app.py