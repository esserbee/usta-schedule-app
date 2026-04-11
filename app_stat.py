import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from flask import Flask, render_template_string, request


app = Flask(__name__)

USTA_SEARCH_URL = 'https://leagues.ustanorcal.com/search.asp'

HTML_TEMPLATE = """<!doctype html>
{% set mode = mode if mode is defined else 'search' %}
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>USTA NorCal Player Statistics</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { --tennis-cursor: url("/static/tennis-cursor.png") 16 16, pointer; }
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 2rem; max-width: 1200px; margin: 0 auto; background: #f7f6f2; color: #222; }
    h1 { font-size: 2.2rem; margin-bottom: 2rem; color: #01696f; }
    h2 { font-size: 1.9rem; margin-bottom: 0.5rem; }
    p { line-height: 1.6; }
    .landing { text-align: center; margin-bottom: 3rem; }
    .intro { max-width: 1000px; margin: 0 auto 3rem auto; text-align: center; }
    .intro-header { margin-bottom: 2rem; text-align: center; }
    .intro-header p { font-size: 1.1rem; color: #555; margin-bottom: 0; }
    .app-container { border: 2px solid #ddd; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    label { font-weight: 600; display: block; margin-bottom: 0.25rem; }
    input { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px; }
    button { background-color: #01696f; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: var(--tennis-cursor); font-weight: 600; }
    button:hover { background-color: #014e54; }
    .status { margin-top: 1rem; padding: 0.75rem; border-radius: 4px; }
    .error { background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
    .success { background-color: #e8f5e8; color: #2e7d32; border: 1px solid #c8e6c9; }
    .results { margin-top: 2rem; }
    .stats-table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
    .stats-table th, .stats-table td { border: 1px solid #ddd; padding: 0.5rem; text-align: center; }
    .stats-table th { background-color: #01696f; color: white; font-weight: 600; }
    .stats-table tr:nth-child(even) { background-color: #f9f9f9; }
    .stats-table .grand-total { background-color: #e8f4f8; font-weight: bold; }
    .stats-table .grand-total td { border-top: 2px solid #01696f; }
    .help { font-size: 0.9rem; color: #666; margin-top: -0.5rem; margin-bottom: 1rem; }
    .loading { margin-top: 1rem; padding: 0.85rem 1rem; border: 1px solid #cfe5e7; background: #eef8f9; border-radius: 4px; color: #014e54; font-weight: 600; }
    .name-search-row { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .name-search-row > div { flex: 1; min-width: 160px; }
    .radio-label { display: flex; align-items: center; gap: 0.5rem; font-weight: normal; cursor: var(--tennis-cursor); }
    .radio-label input { width: auto; margin: 0; }
    .profile-results-list { list-style: none; padding: 0; margin: 0.75rem 0; }
    .profile-results-list li { margin-bottom: 0.5rem; }
    .profile-results-list label { font-weight: 400; display: flex !important; align-items: flex-start; gap: 0.5rem; cursor: pointer; padding: 0.5rem 0.75rem; border-radius: 6px; border: 1px solid #e0e0e0; background: #fafafa; transition: background 0.15s; margin: 0; }
    .profile-results-list label:hover { background: #eef8f9; border-color: #01696f; }
    .profile-results-list input[type="radio"] { margin-top: 0.2rem; flex-shrink: 0; width: auto !important; padding: 0 !important; margin-bottom: 0 !important; }
    .profile-results-list .profile-name { font-weight: 700; color: #01696f; }
    .profile-results-list .profile-meta { font-size: 0.82rem; color: #666; }
    .profile-results-list .profile-expired { color: #a12c2c; font-size: 0.78rem; font-style: italic; }
    .expired-row { opacity: 0.65; }
    .clear-button { background-color: transparent; border: 1px solid #01696f; color: #01696f; }
    .clear-button:hover { background-color: #f0f8f8; }

    @media (max-width: 768px) {
      body { padding: 1rem; }

      h1 { font-size: 1.8rem; margin-bottom: 1rem; }

      h2 { font-size: 1.5rem; }

      .landing,
      .intro,
      .app-container {
        width: 100%;
        max-width: none;
      }

      .intro { margin-bottom: 1.5rem; }

      .intro-header {
        margin-bottom: 1.25rem;
      }

      .intro-header p {
        font-size: 1rem;
        line-height: 1.5;
      }

      .app-container {
        padding: 1rem;
        border-radius: 10px;
      }

      .results {
        margin-top: 1.5rem;
      }

      .help {
        font-size: 0.82rem;
        margin-top: 0.2rem;
        margin-bottom: 0.85rem;
      }

      label {
        margin-bottom: 0.2rem;
      }

      button {
        padding: 0.65rem 1rem;
        font-size: 0.95rem;
      }

      .stats-table th,
      .stats-table td {
        padding: 0.3rem 0.25rem;
        font-size: 0.72rem;
        white-space: normal;
        word-break: break-word;
        overflow-wrap: anywhere;
      }

      .stats-table th { line-height: 1.1; }
    }
  </style>
</head>
<body>
  <div class="landing">
    <div class="app-container">
      <h1>USTA NorCal Player Statistics</h1>
      <div class="intro">
        <div class="intro-header">
          <p>View comprehensive career statistics extracted from your USTA NorCal player profile.</p>
        </div>
      </div>

      <form id="main-generate-form" method="post" action="/analyze">
        <fieldset style="border:none; padding:0; margin:0 0 1rem 0;">
          <legend style="font-weight:600; margin-bottom:0.5rem;">Input Method</legend>
          <div style="display:flex; flex-direction:column; gap:0.5rem;">
            <label class="radio-label">
              <input type="radio" name="mode" value="search" onchange="toggleModeInputs()" {% if mode == 'search' %}checked{% endif %}> Search by name
            </label>
            <label class="radio-label">
              <input type="radio" name="mode" value="profile" onchange="toggleModeInputs()" {% if mode == 'profile' %}checked{% endif %}> Player profile URL
            </label>
          </div>
        </fieldset>

        <div id="search-input" {% if mode != 'search' %}style="display:none;"{% endif %}>
          <div class="name-search-row">
            <div>
              <label for="first_name">First name (optional if last name given)</label>
              <input type="text" id="first_name" name="first_name" placeholder="e.g. John" value="{{ first_name or '' }}" autocomplete="given-name">
            </div>
            <div>
              <label for="last_name">Last name (optional if first name given)</label>
              <input type="text" id="last_name" name="last_name" placeholder="e.g. Smith" value="{{ last_name or '' }}" autocomplete="family-name">
            </div>
          </div>
          <div class="help">Search for a player on the USTA NorCal website by name.</div>
        </div>

        <div id="profile-input" {% if mode != 'profile' %}style="display:none;"{% endif %}>
          <label for="profile_url">Player profile URL</label>
          <input type="url" id="profile_url" name="profile_url" placeholder="https://leagues.ustanorcal.com/...playermatches.asp?id=..." value="{{ profile_url or '' }}">
          <div class="help">Enter your USTA NorCal player profile URL to extract career statistics.</div>
        </div>
        
        <button type="submit">Analyze Statistics</button>
      </form>

      <div id="loading-message" class="loading" style="display:none;" aria-live="polite">Analyzing player statistics... please wait.</div>

      {% if message %}
      <div class="status {% if error %}error{% else %}success{% endif %}">
        {{ message }}
      </div>
      {% endif %}
    </div>
  </div>

  {% if profile_choices %}
  <div class="results">
    <div class="app-container">
      <h2>Select your profile</h2>
      <p class="embedded-intro-copy">Found {{ profile_choices | length }} result(s) for <strong>{{ search_query }}</strong>. Select the correct profile below.</p>
      <form id="profile-select-form" method="post" action="/analyze">
        <fieldset style="border:none; padding:0; margin:0;">
          <input type="hidden" name="mode" value="profile">
          <ul class="profile-results-list">
          {% for p in profile_choices %}
            <li class="{% if p.expired %}expired-row{% endif %}">
              <label>
                <input type="radio" name="profile_url" value="{{ p.url }}" {% if loop.first and not p.expired %}checked{% endif %}>
                <span>
                  <span class="profile-name">{{ p.name }}</span>
                  {% if p.city %}<span class="profile-meta"> &mdash; {{ p.city }}</span>{% endif %}
                  {% if p.usta_number %}<span class="profile-meta"> &middot; USTA #{{ p.usta_number }}</span>{% endif %}
                  {% if p.expired %}<span class="profile-expired"> (membership expired {{ p.expiration }})</span>{% endif %}
                </span>
              </label>
            </li>
          {% endfor %}
          </ul>
          <button type="submit">Analyze This Profile</button>
          <button type="button" class="clear-button" onclick="window.location.href='/';" style="margin-left: 1rem;">Search Another Name</button>
          <div id="profile-select-loading" class="loading" style="display:none;" aria-live="polite">Loading profile... please wait.</div>
        </fieldset>
      </form>
    </div>
  </div>
  {% endif %}

  {% if player_stats %}
  <div class="results">
    <div class="app-container">
    <h2>{{ player_name }} - Career Statistics</h2>
    <p class="help">Statistics extracted from player profile. Data includes all teams and divisions across all years.</p>
    <table class="stats-table">
      <thead>
        <tr>
          <th>Year</th>
          <th>Total Matches</th>
          <th>Wins</th>
          <th>Losses</th>
          <th>Win %</th>
          <th>Singles</th>
          <th>Doubles</th>
          <th>Regular Season</th>
          <th>Post Season</th>
        </tr>
      </thead>
      <tbody>
        {% for year, stats in player_stats.by_year.items()|sort(reverse=true) %}
        <tr>
          <td>{{ year }}</td>
          <td>{{ stats.total_matches }}</td>
          <td>{{ stats.wins }}</td>
          <td>{{ stats.losses }}</td>
          <td>{{ "%.1f"|format(stats.win_percentage) }}%</td>
          <td>{{ stats.singles }}</td>
          <td>{{ stats.doubles }}</td>
          <td>{{ stats.regular_season }}</td>
          <td>{{ stats.postseason }}</td>
        </tr>
        {% endfor %}
        <tr class="grand-total">
          <td><strong>Total</strong></td>
          <td><strong>{{ player_stats.grand_total.total_matches }}</strong></td>
          <td><strong>{{ player_stats.grand_total.wins }}</strong></td>
          <td><strong>{{ player_stats.grand_total.losses }}</strong></td>
          <td><strong>{{ "%.1f"|format(player_stats.grand_total.win_percentage) }}%</strong></td>
          <td><strong>{{ player_stats.grand_total.singles }}</strong></td>
          <td><strong>{{ player_stats.grand_total.doubles }}</strong></td>
          <td><strong>{{ player_stats.grand_total.regular_season }}</strong></td>
          <td><strong>{{ player_stats.grand_total.postseason }}</strong></td>
        </tr>
      </tbody>
    </table>
    
    {% if team_details %}
    <h3>Team Details</h3>
    <table class="stats-table">
      <thead>
        <tr>
          <th>Year</th>
          <th>Division</th>
          <th>Team</th>
          <th>Role</th>
          <th>Win/Loss</th>
          <th>Win %</th>
          <th>Singles</th>
          <th>Doubles</th>
          <th>Post Season</th>
        </tr>
      </thead>
      <tbody>
        {% for team in team_details|sort(attribute='year', reverse=true) %}
        <tr>
          <td>{{ team.year }}</td>
          <td>{{ team.division }}</td>
          <td>{{ team.team }}</td>
          <td>{{ team.captain_role or '-' }}</td>
          <td>{{ team.win_loss }}</td>
          <td>{{ "%.1f"|format(team.win_percent) }}%</td>
          <td>{{ team.singles_count or '-' }}</td>
          <td>{{ team.doubles_count or '-' }}</td>
          <td>{{ team.postseason_count or '-' }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% endif %}
    </div>
  </div>
  {% endif %}

  <script>
    function toggleModeInputs() {
      const mode = document.querySelector('input[name="mode"]:checked');
      if (!mode) return;
      const searchWrap = document.getElementById('search-input');
      const profileWrap = document.getElementById('profile-input');
      
      searchWrap.style.display = 'none';
      profileWrap.style.display = 'none';
      
      const submitBtn = document.querySelector('#main-generate-form button[type="submit"]');

      if (mode.value === 'search') {
        searchWrap.style.display = 'block';
        if (submitBtn) submitBtn.textContent = 'Search';
      } else {
        profileWrap.style.display = 'block';
        if (submitBtn) submitBtn.textContent = 'Analyze';
      }
    }
    
    // Call immediately to set initial state (covers document.write re-rendering)
    toggleModeInputs();
    document.addEventListener('DOMContentLoaded', toggleModeInputs);

    const mainForm = document.getElementById('main-generate-form');
    if (mainForm) {
      mainForm.addEventListener('submit', function(e) {
        const mode = document.querySelector('input[name="mode"]:checked');
        if (mode && mode.value === 'search') {
          e.preventDefault();
          const firstName = document.getElementById('first_name').value.trim();
          const lastName = document.getElementById('last_name').value.trim();
          if (!firstName && !lastName) {
            alert('Please enter at least a first name or last name to search.');
            return;
          }
          const btn = mainForm.querySelector('button[type="submit"]');
          if (btn) { btn.disabled = true; btn.textContent = 'Searching...'; }
          const loadingEl = document.getElementById('loading-message');
          if (loadingEl) {
            loadingEl.textContent = 'Searching for player... please wait.';
            loadingEl.style.display = 'block';
          }
          const fd = new FormData();
          fd.append('first_name', firstName);
          fd.append('last_name', lastName);
          fetch('/search_player_stats', { method: 'POST', body: fd })
            .then(r => r.text())
            .then(html => {
              document.open();
              document.write(html);
              document.close();
            })
            .catch(err => {
              if (btn) { btn.disabled = false; btn.textContent = 'Analyze Statistics'; }
              if (loadingEl) loadingEl.style.display = 'none';
              alert('Search failed: ' + err.message);
            });
        } else {
          e.preventDefault();
          const loading = document.getElementById('loading-message');
          const submitButton = mainForm.querySelector('button[type="submit"]');
          if (loading) {
            loading.textContent = 'Analyzing player statistics... please wait.';
            loading.style.display = 'block';
          }
          if (submitButton) {
            submitButton.dataset.originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Analyzing...';
          }
          setTimeout(function() { mainForm.submit(); }, 50);
        }
      });
    }

    const profileSelectForm = document.getElementById('profile-select-form');
    if (profileSelectForm) {
      profileSelectForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const loading = document.getElementById('profile-select-loading');
        const submitButton = profileSelectForm.querySelector('button[type="submit"]');
        if (loading) loading.style.display = 'block';
        if (submitButton) {
          submitButton.disabled = true;
          submitButton.textContent = 'Analyzing...';
        }
        setTimeout(function() { profileSelectForm.submit(); }, 100);
      });
    }
  </script>
</body>
</html>
"""


def extract_player_name_from_profile(html):
    """Best-effort extraction of the player name from a profile page."""
    soup = BeautifulSoup(html, 'html.parser')

    blacklist = {
        'usta', 'northern', 'california', 'norcal', 'login', 'join', 'search', 'calendar',
        'play', 'improve', 'stay current', 'coach', 'organize', 'organize', 'pro tennis',
        'captain', 'email', 'administrator'
    }

    def clean(txt):
        return re.sub(r'\s+', ' ', (txt or '').strip())

    # Common: name appears near the top in <b>/<strong> inside a header table.
    candidate_re = re.compile(r"^[A-Z][a-zA-Z.\-']+(?:\s+[A-Z][a-zA-Z.\-']+)+$")

    for tag in soup.find_all(['strong', 'b']):
        txt = clean(tag.get_text(' ', strip=True))
        if not txt:
            continue
        if len(txt) > 60 or len(txt) < 3:
            continue
        low = txt.lower()
        if any(b in low for b in blacklist):
            continue
        if candidate_re.match(txt):
            return txt

    # Fallback: regex across whole page text (first plausible "First Last" name).
    page_text = clean(soup.get_text(' ', strip=True))
    m = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', page_text)
    if m:
        return m.group(1).strip()

    return ''


def parse_match_results_from_profile(html, player_name):
    """Parse match results from a player profile page."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for match results/match history section on the profile
    # USTA profiles often have different table structures
    tables = soup.find_all('table')
    results_table = None
    
    # First try: Look for tables with match-related headers
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) < 2:
            continue
            
        # Check header row for match-related columns
        header_cells = rows[0].find_all(['td', 'th'])
        header_text = ' '.join(cell.get_text(' ', strip=True).lower() for cell in header_cells)
        
        if any(keyword in header_text for keyword in ['date', 'opponent', 'score', 'match', 'result', 'team', 'vs']):
            results_table = table
            break
    
    # Second try: Look for tables that contain date patterns in their rows
    if not results_table:
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text(' ', strip=True)
                    # Look for date patterns or score patterns
                    if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text) or re.search(r'\d+-\d+', text):
                        results_table = table
                        break
                if results_table:
                    break
            if results_table:
                break
    
    if not results_table:
        return []
    
    matches = []
    rows = results_table.find_all('tr')[1:]  # Skip header
    
    header_cells = results_table.find_all('tr')[0].find_all(['td', 'th'])
    headers = [cell.get_text(' ', strip=True) for cell in header_cells]
    
    for tr in rows:
        cells = tr.find_all(['td', 'th'])
        if len(cells) < len(headers):
            continue
        
        # Extract data from cells
        cell_texts = [cell.get_text(' ', strip=True) for cell in cells]
        
        # Skip empty rows or rows with no data
        if not any(cell_texts) or all(text in ['-', ''] for text in cell_texts):
            continue
        
        # Parse based on the observed structure:
        # ['Divisions (results)', 'Teams', 'Win/Loss', 'Winning percent', 'Singles', 'Doubles', 'Post season matches']
        
        division = cell_texts[0] if len(cell_texts) > 0 else ''
        team = cell_texts[1] if len(cell_texts) > 1 else ''
        win_loss = cell_texts[2] if len(cell_texts) > 2 else ''
        win_percent = cell_texts[3] if len(cell_texts) > 3 else ''
        singles = cell_texts[4] if len(cell_texts) > 4 else ''
        doubles = cell_texts[5] if len(cell_texts) > 5 else ''
        postseason = cell_texts[6] if len(cell_texts) > 6 else ''
        
        # Extract year from division name
        year_match = re.search(r'\b(20\d{2})\b', division)
        year = int(year_match.group()) if year_match else datetime.now().year
        
        # Parse win/loss (format like "5 / 3")
        wins = 0
        losses = 0
        win_pct = 0.0
        if win_loss and '/' in win_loss:
            parts = win_loss.split('/')
            try:
                wins = int(parts[0].strip())
                losses = int(parts[1].strip()) if len(parts) > 1 else 0
                if wins + losses > 0:
                    win_pct = (wins / (wins + losses)) * 100
            except ValueError:
                pass
        
        # Parse singles/doubles counts
        singles_count = 0
        doubles_count = 0
        postseason_count = 0
        
        try:
            if singles and singles != '-':
                singles_count = int(singles)
            if doubles and doubles != '-':
                doubles_count = int(doubles)
            if postseason and postseason != '-':
                postseason_count = int(postseason)
        except ValueError:
            pass
        
        # Extract captain/co-captain info from team name
        captain_role = ''
        clean_team = team
        if 'Co-Captain' in team:
            captain_role = 'Co-Captain'
            clean_team = team.replace(' Co-Captain', '').replace('Co-Captain ', '')
        elif 'Captain' in team:
            captain_role = 'Captain'
            clean_team = team.replace(' Captain', '').replace('Captain ', '')
        
        # Remove year from division (keep only league type and level)
        clean_division = re.sub(r'\b20\d{2}\b', '', division).strip()
        
        # Only include if we have actual match data
        total_matches = wins + losses
        if total_matches > 0:
            matches.append({
                'date': str(year),  # Use year as date for aggregation
                'opponent': team,
                'score': f"{wins}/{losses}",
                'is_win': wins > losses,  # Team winning record
                'match_type': 'postseason' if postseason_count > 0 else 'regular',
                'is_singles': singles_count > 0,
                'is_doubles': doubles_count > 0,
                'team': clean_team.strip(),
                'year': year,
                'wins': wins,
                'losses': losses,
                'singles_count': singles_count,
                'doubles_count': doubles_count,
                'postseason_count': postseason_count,
                'division': clean_division,
                'win_percent': win_pct,
                'captain_role': captain_role,
                'win_loss': f"{wins} / {losses}"  # Add explicit win_loss field
            })
    
    return matches


def compute_player_statistics(all_matches, player_name):
    """Compute comprehensive statistics from all matches."""
    stats_by_year = {}
    
    for match in all_matches:
        year = match['year']
        if year not in stats_by_year:
            stats_by_year[year] = {
                'total_matches': 0,
                'wins': 0,
                'losses': 0,
                'singles': 0,
                'doubles': 0,
                'regular_season': 0,
                'postseason': 0
            }
        
        stats = stats_by_year[year]
        
        # For profile data, each match record represents a team's season
        # Use the aggregated values directly
        if 'wins' in match and 'losses' in match:
            # Profile data format
            stats['total_matches'] += match['wins'] + match['losses']
            stats['wins'] += match['wins']
            stats['losses'] += match['losses']
            stats['singles'] += match.get('singles_count', 0)
            stats['doubles'] += match.get('doubles_count', 0)
            stats['postseason'] += match.get('postseason_count', 0)
            stats['regular_season'] += (match['wins'] + match['losses']) - match.get('postseason_count', 0)
        else:
            # Individual match format (fallback)
            stats['total_matches'] += 1
            if match['is_win']:
                stats['wins'] += 1
            else:
                stats['losses'] += 1
            if match['is_singles']:
                stats['singles'] += 1
            if match['is_doubles']:
                stats['doubles'] += 1
            if match['match_type'] == 'regular':
                stats['regular_season'] += 1
            elif match['match_type'] == 'postseason':
                stats['postseason'] += 1
    
    # Calculate win percentages
    for year, stats in stats_by_year.items():
        if stats['total_matches'] > 0:
            stats['win_percentage'] = (stats['wins'] / stats['total_matches']) * 100
        else:
            stats['win_percentage'] = 0
    
    # Calculate grand totals
    grand_total = {
        'total_matches': sum(s['total_matches'] for s in stats_by_year.values()),
        'wins': sum(s['wins'] for s in stats_by_year.values()),
        'losses': sum(s['losses'] for s in stats_by_year.values()),
        'singles': sum(s['singles'] for s in stats_by_year.values()),
        'doubles': sum(s['doubles'] for s in stats_by_year.values()),
        'regular_season': sum(s['regular_season'] for s in stats_by_year.values()),
        'postseason': sum(s['postseason'] for s in stats_by_year.values())
    }
    
    if grand_total['total_matches'] > 0:
        grand_total['win_percentage'] = (grand_total['wins'] / grand_total['total_matches']) * 100
    else:
        grand_total['win_percentage'] = 0
    
    return stats_by_year, grand_total


def search_player_by_name_stats():
    first_name = request.form.get('first_name', '').strip()
    last_name  = request.form.get('last_name', '').strip()

    if not first_name and not last_name:
        return render_template_string(
            HTML_TEMPLATE,
            message='Please enter a first name and/or last name to search.',
            error=True,
            mode='search',
            first_name=first_name,
            last_name=last_name,
            profile_choices=None,
            search_query='',
            profile_url='',
            player_stats=None,
            player_name=None,
            team_details=None,
        )

    # Build query string — USTA NorCal search works best with "Last, First"
    if last_name and first_name:
        search_text = f"{last_name}, {first_name}"
    elif last_name:
        search_text = last_name
    elif first_name:
        # Trick to search by first name only on this legacy site
        search_text = f", {first_name}"
    else:
        search_text = ""
        
    search_query = search_text.strip(', ') if search_text else ''

    try:
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        get_resp = session.get(USTA_SEARCH_URL, timeout=15)
        get_resp.raise_for_status()
        get_soup = BeautifulSoup(get_resp.text, 'html.parser')
        
        token = ''
        token_input = get_soup.find('input', {'name': 'token'})
        if token_input and token_input.get('value'):
            token = token_input.get('value')
            
        post_data = {
            'lstsearch': '2',
            'searchfor': '2',
            'name': search_text,
            'cmd': ' Search '
        }
        if token:
            post_data['token'] = token
            
        resp = session.post(USTA_SEARCH_URL, data=post_data, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            message=f'Error contacting USTA NorCal search: {e}',
            error=True,
            mode='search',
            first_name=first_name,
            last_name=last_name,
            profile_choices=None,
            search_query=search_query,
            profile_url='',
            player_stats=None,
            player_name=None,
            team_details=None,
        )

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Exact logic from app_schedule.py to prevent differences
    profile_choices = []
    seen_urls = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'playermatches.asp' not in href.lower():
            continue
        full_url = urljoin(USTA_SEARCH_URL, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        row = a.find_parent('tr')
        name = a.get_text(' ', strip=True)
        city = ''
        usta_number = ''
        expiration = ''
        expired = False

        if row:
            tds = row.find_all('td')
            cells = [td.get_text(' ', strip=True) for td in tds]
            if cells:
                name = cells[0] if cells[0] else name
            if len(cells) >= 2:
                city = cells[1]
            if len(cells) >= 3:
                usta_number = cells[2]
            if len(cells) >= 4:
                expiration = cells[3]
                try:
                    exp_dt = datetime.strptime(expiration, '%m/%d/%Y')
                    if exp_dt < datetime.now():
                        expired = True
                except Exception:
                    pass

        profile_choices.append({
            'url': full_url,
            'name': name,
            'city': city,
            'usta_number': usta_number,
            'expiration': expiration,
            'expired': expired,
        })

    if not profile_choices:
        return render_template_string(
            HTML_TEMPLATE,
            message=f'No players found matching "{search_query}". Try a different spelling or use the profile URL directly.',
            error=True,
            mode='search',
            first_name=first_name,
            last_name=last_name,
            profile_choices=None,
            search_query=search_query,
            profile_url='',
            player_stats=None,
            player_name=None,
            team_details=None,
        )

    return render_template_string(
        HTML_TEMPLATE,
        message=None,
        error=False,
        mode='search',
        first_name=first_name,
        last_name=last_name,
        profile_choices=profile_choices,
        search_query=search_query,
        profile_url='',
        player_stats=None,
        player_name=None,
        team_details=None,
    )

def stats_analyze():
    mode = request.form.get('mode', 'profile')
    
    if mode == 'search':
        return search_player_by_name_stats()
        
    profile_url = request.form.get('profile_url', '').strip()
    
    if not profile_url:
        return render_template_string(
            HTML_TEMPLATE,
            message="Please provide a player profile URL.",
            error=True,
            profile_url=profile_url,
            player_stats=None,
            player_name=None,
            team_details=None
        )
    
    try:
        resp = requests.get(profile_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            message=f"Error fetching profile: {e}",
            error=True,
            profile_url=profile_url,
            player_stats=None,
            player_name=None,
            team_details=None
        )

    player_name = extract_player_name_from_profile(resp.text).strip()
    
    # Parse match results from player profile
    try:
        all_matches = parse_match_results_from_profile(resp.text, player_name)
        
        if not all_matches:
            return render_template_string(
                HTML_TEMPLATE,
                message="Could not find any match statistics on that profile.",
                error=True,
                profile_url=profile_url,
                player_stats=None,
                player_name=player_name,
                team_details=None
            )
        
        # Compute statistics
        stats_by_year, grand_total = compute_player_statistics(all_matches, player_name)
        player_stats = {
            'by_year': stats_by_year,
            'grand_total': grand_total
        }
        
        return render_template_string(
            HTML_TEMPLATE,
            message=f"Successfully analyzed statistics for {player_name}. Found {len(all_matches)} team records across {len(stats_by_year)} years.",
            error=False,
            profile_url=profile_url,
            player_stats=player_stats,
            player_name=player_name,
            team_details=all_matches
        )
        
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            message=f"Error analyzing profile: {e}",
            error=True,
            profile_url=profile_url,
            player_stats=None,
            player_name=player_name,
            team_details=None
        )


@app.route('/', methods=['GET'])
def index():
    return render_template_string(
        HTML_TEMPLATE,
        message=None,
        error=False,
        profile_url='',
        player_stats=None,
        player_name=None,
        team_details=None,
    )


@app.route('/analyze', methods=['POST'])
def analyze():
    return stats_analyze()


@app.route('/search_player_stats', methods=['POST'])
def search_player_stats_route():
    return search_player_by_name_stats()


if __name__ == '__main__':
    app.run(debug=True, port=5002)


