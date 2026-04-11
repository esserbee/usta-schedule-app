# 🎾 USTA NorCal League Tools

A premium web suite for USTA NorCal tennis players and captains to manage schedules and analyze statistics effortlessly. 

## ✨ Key Features

### 📅 Unified Schedule Organizer (`app_schedule.py`)
Combine match schedules from multiple teams into one clean, conflict-aware interface.
- **Player Name Search:** Find your USTA profile instantly by searching for your first or last name. No more hunting for URLs!
- **Conflict Detection:** Visual highlighting of overlapping matches to help you manage your availability.
- **Export Options:** 
  - 📆 **Calendar:** One-click download of `.ics` files to sync with Apple/Google/Microsoft calendars.
  - 📊 **Excel:** Clean, sorted `.xlsx` exports for offline sharing and tracking.
- **Smart Parsing:** Automatic detection of home/away status, location parsing, and start times.

### 📊 Comprehensive Career Stats (`app_stat.py`)
Deep-dive into your historical performance data extracted directly from USTA NorCal records.
- **Name Search Integration:** Search by name to pull your full performance history.
- **Tennis Record Integration:** Automatically pulls your **Estimated Dynamic Rating** and yearly win/loss record from TennisRecord.com for cross-reference.
- **Yearly Performance:** Year-by-year wins, losses, and win percentages.
- **Match Breakdown:** Detailed metrics for singles vs. doubles and regular season vs. postseason.
- **Team History:** Review every team you've played for, including captaincy roles and playoff runs.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `pip`

### Local Installation
1. Clone the repository and navigate to the directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the unified application:
   ```bash
   python app.py
   ```
4. Open your browser to `http://localhost:5000`.

### Using the Search
The application supports a flexible search system:
- **Last Name Only:** e.g., "Doe"
- **First Name Only:** e.g., "John" (uses a specialized query format for USTA compatibility)
- **Full Name:** e.g., "Doe, John" for precise matching.

---
*Created with ❤️ for the NorCal Tennis Community.*
