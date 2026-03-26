# USTA NorCal League Tools

A web application for USTA NorCal tennis players and team captains with two main tools:

## 📅 Schedule Organizer

Combine league match schedules from multiple teams and detect scheduling conflicts.

**Features:**
- Input via player profile URL (auto-discover teams) or direct team URLs
- Smart location parsing from match details
- Visual conflict highlighting for overlapping matches
- Export schedules to Excel with formatting
- Color-coded home/away status

## 📊 Player Statistics

Extract and display career statistics from USTA NorCal player profiles.

**Features:**
- Year-by-year win/loss records and percentages
- Breakdown by match type (singles/doubles, regular/postseason)
- Grand totals across all years
- Detailed team participation history

## Setup & Usage

```bash
pip install flask requests pandas beautifulsoup4 openpyxl
python app.py
```

Visit `http://localhost:5000` and choose between the two tools. Enter your USTA profile or team URLs to get started.

**Note:** Requires valid USTA NorCal player profile or team info page URLs.
