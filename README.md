# USTA NorCal League Tools

A web application for USTA NorCal tennis players and team captains with two main tools:

## 📅 Schedule Organizer

Combine league match schedules from multiple teams and detect scheduling conflicts.

**Features:**
- ✨ Input via player profile URL (auto-discover teams) or direct team URLs
- 🚀 Export directly to your Calendar (.ics format) or formatted Excel (.xlsx) files
- 📍 Smart location parsing and home/away status detection
- ⚖️ Visual highlight markers for overlapping match conflicts

## 📊 Player Statistics

Extract and display career statistics from USTA NorCal player profiles.

**Features:**
- 📈 Year-by-year win/loss records and percentages
- 🎾 Breakdown by match type (singles/doubles, regular/postseason)
- 🧮 Grand totals across all active years
- 👟 Detailed team participation history

## Setup & Deployment

**Local Usage:**
```bash
pip install -r requirements.txt
python app.py
```
Visit `http://localhost:5000`. Enter your USTA profile or team URLs to get started.

**Cloud / Docker Deployment:**
This application is fully containerized. A `Dockerfile` and `gunicorn` configuration are provided for zero-config deployments to services like Google Cloud Run or AWS.

> **Note:** Requires valid USTA NorCal player profile or team info page URLs. 
