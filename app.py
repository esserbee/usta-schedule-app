from flask import Flask, request, send_file, render_template_string
import io
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

app = Flask(__name__)

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>USTA NorCal League Schedule Organizer</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 2rem; max-width: 1000px; margin: 0 auto; background: #f7f6f2; color: #222; }
    h1 { font-size: 1.9rem; margin-bottom: 0.5rem; }
    p { max-width: 70ch; }
    label { font-weight: 600; display: block; margin-bottom: 0.25rem; }
    textarea { width: 100%; min-height: 140px; padding: 0.75rem; border-radius: 8px; border: 1px solid #ccc; font-family: monospace; font-size: 0.9rem; }
    input[type="url"] { width: 100%; padding: 0.6rem 0.75rem; border-radius: 8px; border: 1px solid #ccc; font-size: 0.9rem; margin-bottom: 0.5rem; }
    button { margin-top: 1rem; padding: 0.6rem 1.2rem; border-radius: 999px; border: none; background: #01696f; color: #fff; font-weight: 600; cursor: pointer; }
    button:hover { background: #0c4e54; }
    .help { font-size: 0.85rem; color: #666; margin-top: 0.25rem; }
    .status { margin-top: 1rem; font-size: 0.9rem; color: #444; }
    .error { color: #a12c2c; }
    code { background: #f0efea; padding: 0.1rem 0.3rem; border-radius: 4px; }
    .results { margin-top: 2rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }
    th, td { border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; }
    th { background: #eceae3; font-weight: 700; }
    tr.conflict { background: #fff7c2; }
    .actions { margin-top: 1rem; }
    .team-list label { font-weight: 400; }
  </style>
</head>
<body>
  <h1>USTA NorCal League Schedule Organizer</h1>
  <p>Paste your USTA NorCal player profile URL to pick your current-year teams, or paste team info URLs directly. The app will fetch schedules, show a combined table, and let you download an Excel file with conflicts highlighted.</p>

  <form method="post" action="/generate">
    <label for="profile_url">Player profile URL (optional)</label>
    <input type="url" id="profile_url" name="profile_url" placeholder="https://leagues.ustanorcal.com/...player..." value="{{ profile_url or '' }}">

    <label for="urls">Team info URLs (optional)</label>
    <textarea id="urls" name="urls" placeholder="https://leagues.ustanorcal.com/teaminfo.asp?id=109510
https://leagues.ustanorcal.com/teaminfo.asp?id=109621">{{ urls_value or '' }}</textarea>
    <div class="help">You can either select teams from your profile above, paste team URLs here, or do both.</div>
    <button type="submit">Generate Schedule</button>
  </form>

  {% if message %}
  <div class="status {% if error %}error{% endif %}">{{ message }}</div>
  {% endif %}

  {% if team_choices %}
  <div class="results">
    <h2>Select teams for {{ current_year }}</h2>
    {% if filtered_to_year %}
      <p>Showing teams detected for {{ current_year }} from your profile. Select which ones to include in the schedule.</p>
    {% else %}
      <p>These are the teams found on your profile. Select which ones to include in the schedule.</p>
    {% endif %}
    <form method="post" action="/generate">
      <input type="hidden" name="profile_url" value="{{ profile_url | e }}">
      <div class="team-list">
      {% for t in team_choices %}
        <div>
          <label>
            <input type="checkbox" name="team_urls" value="{{ t.url }}" checked>
            {{ t.label }}{% if t.context %} — {{ t.context }}{% endif %}
          </label>
        </div>
      {% endfor %}
      </div>
      <button type="submit">Build Schedule from Selected Teams</button>
    </form>
  </div>
  {% endif %}

  {% if schedule %}
  <div class="results">
    <h2>Combined schedule</h2>
    <p>Rows highlighted in yellow are days where you have more than one match scheduled.</p>
    <table class="schedule-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Team name</th>
          <th>Match time</th>
          <th>All start times / lanes</th>
          <th>Opponent team</th>
          <th>Home/Away</th>
        </tr>
      </thead>
      <tbody>
        {% for row in schedule %}
        <tr class="{% if row.Is_conflict %}conflict{% endif %}">
          <td>{{ row.Date_display }}</td>
          <td>{{ row['Team name'] }}</td>
          <td>{{ row['Match time'] }}</td>
          <td>{{ row['All start times / lanes'] }}</td>
          <td>{{ row['Opponent team'] }}</td>
          <td>{{ row['Home/Away'] }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <div class="actions">
      <form method="post" action="/download">
        <input type="hidden" name="urls" value="{{ urls_value | e }}">
        <button type="submit">Download Excel Schedule</button>
      </form>
    </div>
  </div>
  {% endif %}
</body>
</html>
"""

time_re = re.compile(r"(\d{1,2}:\d{2}\s*(?:AM|PM))", re.IGNORECASE)


def extract_team_name(soup, fallback):
    if soup.title and '|' in soup.title.get_text():
        return soup.title.get_text().split('|')[-1].strip()
    h1 = soup.find('h1') or soup.find('h2')
    if h1:
        return h1.get_text(strip=True)
    return fallback


def parse_schedule_html(html, fallback_name):
    soup = BeautifulSoup(html, 'html.parser')
    team_name = extract_team_name(soup, fallback_name)

    b_tags = soup.find_all(['b', 'strong'])
    schedule_table = None
    for b in b_tags:
        if 'team schedule' in b.get_text(strip=True).lower():
            for tbl in b.find_all_next('table'):
                header_tr = tbl.find('tr')
                if not header_tr:
                    continue
                header_text = ' '.join(td.get_text(' ', strip=True) for td in header_tr.find_all('td'))
                if 'Match date' in header_text:
                    schedule_table = tbl
                    break
        if schedule_table:
            break

    rows_out = []
    if not schedule_table:
        return rows_out

    for tr in schedule_table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 9:
            continue
        header_candidate = ' '.join(td.get_text(' ', strip=True) for td in tds[:5])
        if 'Match date' in header_candidate or 'Status' in header_candidate:
            continue
        status = tds[0].get_text(' ', strip=True)
        if not status:
            continue

        date_text = tds[2].get_text(' ', strip=True).replace(' ', '').strip()
        day_text = tds[3].get_text(' ', strip=True)

        time_cell_raw = tds[4].get_text(' ', strip=True)
        full_time = time_cell_raw
        for phrase in ['Last schedule update', 'User:']:
            idx = full_time.find(phrase)
            if idx != -1:
                full_time = full_time[:idx].strip(' .;,')

        m = time_re.search(time_cell_raw)
        if m:
            match_time = m.group(1).upper().replace(' ', '')
        else:
            match_time = ''

        opp_cell = tds[5].get_text(' ', strip=True)
        home_away = tds[6].get_text(' ', strip=True)

        rows_out.append({
            'Date_raw': date_text,
            'Day': day_text,
            'Team name': team_name,
            'Match time': match_time,
            'All start times / lanes': full_time,
            'Opponent team': opp_cell,
            'Home/Away': home_away,
            'Status': status,
        })

    return rows_out


def parse_profile_for_teams(html, base_url):
    """Extract team links from a player profile page.

    Heuristic: look for anchors whose href contains 'teaminfo.asp?id='. Use
    surrounding row text as context to help identify the season/year.
    """
    soup = BeautifulSoup(html, 'html.parser')
    teams = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'teaminfo.asp' in href.lower():
            full_url = urljoin(base_url, href)
            label = a.get_text(' ', strip=True) or 'Team'
            row = a.find_parent('tr')
            context = row.get_text(' ', strip=True) if row else ''
            teams.append({'url': full_url, 'label': label, 'context': context})
    return teams


def build_schedule(urls):
    all_rows = []
    for url in urls:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        fallback_name = url
        rows = parse_schedule_html(resp.text, fallback_name)
        if not rows:
            raise ValueError(f"Could not find a schedule table on {url}.")
        all_rows.extend(rows)

    if not all_rows:
        raise ValueError("No matches found in the provided pages.")

    df = pd.DataFrame(all_rows)
    df['Date'] = pd.to_datetime(df['Date_raw'], format='%m/%d/%y', errors='coerce')
    df = df.sort_values(by=['Date', 'Match time', 'Team name']).reset_index(drop=True)

    out_df = df[['Date', 'Team name', 'Match time', 'All start times / lanes', 'Opponent team', 'Home/Away']].copy()

    # Mark conflicting dates
    counts = out_df['Date'].value_counts(dropna=False)
    conflict_dates = set(counts[counts > 1].index)
    out_df['Is_conflict'] = out_df['Date'].isin(conflict_dates)

    # Date display string, e.g., "Apr 15"
    out_df['Date_display'] = out_df['Date'].dt.strftime('%b %d').str.replace(' 0', ' ', regex=False)

    return out_df


@app.route('/', methods=['GET'])
def index():
    current_year = datetime.now().year
    return render_template_string(
        HTML_TEMPLATE,
        urls_value='',
        profile_url='',
        schedule=None,
        message=None,
        error=False,
        team_choices=None,
        current_year=current_year,
        filtered_to_year=False,
    )


@app.route('/generate', methods=['POST'])
def generate():
    urls_raw = request.form.get('urls', '')
    profile_url = request.form.get('profile_url', '').strip()
    selected_team_urls = request.form.getlist('team_urls')
    current_year = datetime.now().year

    # Stage 2: user selected teams from profile
    if selected_team_urls:
        urls = selected_team_urls
        try:
            out_df = build_schedule(urls)
        except Exception as e:
            return render_template_string(
                HTML_TEMPLATE,
                message=str(e),
                error=True,
                urls_value='
'.join(urls),
                profile_url=profile_url,
                schedule=None,
                team_choices=None,
                current_year=current_year,
                filtered_to_year=True,
            )

        schedule = out_df.to_dict(orient='records')
        return render_template_string(
            HTML_TEMPLATE,
            message=None,
            error=False,
            urls_value='
'.join(urls),
            profile_url=profile_url,
            schedule=schedule,
            team_choices=None,
            current_year=current_year,
            filtered_to_year=True,
        )

    # Stage 1: profile URL given, no team selection yet, and no manual URLs
    if profile_url and not urls_raw:
        try:
            resp = requests.get(profile_url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return render_template_string(
                HTML_TEMPLATE,
                message=f"Error fetching profile: {e}",
                error=True,
                urls_value=urls_raw,
                profile_url=profile_url,
                schedule=None,
                team_choices=None,
                current_year=current_year,
                filtered_to_year=False,
            )

        teams = parse_profile_for_teams(resp.text, profile_url)
        if not teams:
            return render_template_string(
                HTML_TEMPLATE,
                message="Could not find any team links on that profile. You can paste team URLs manually instead.",
                error=True,
                urls_value=urls_raw,
                profile_url=profile_url,
                schedule=None,
                team_choices=None,
                current_year=current_year,
                filtered_to_year=False,
            )

        # Filter for current-year teams if possible
        year_str = str(current_year)
        current_teams = [t for t in teams if year_str in t.get('context', '') or year_str in t.get('label', '')]
        if current_teams:
            team_choices = current_teams
            filtered_to_year = True
        else:
            team_choices = teams
            filtered_to_year = False

        return render_template_string(
            HTML_TEMPLATE,
            message=None,
            error=False,
            urls_value=urls_raw,
            profile_url=profile_url,
            schedule=None,
            team_choices=team_choices,
            current_year=current_year,
            filtered_to_year=filtered_to_year,
        )

    # Manual URLs path (existing behavior)
    urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
    if not urls:
        return render_template_string(
            HTML_TEMPLATE,
            message="Please paste at least one team URL or provide a player profile URL.",
            error=True,
            urls_value=urls_raw,
            profile_url=profile_url,
            schedule=None,
            team_choices=None,
            current_year=current_year,
            filtered_to_year=False,
        )

    try:
        out_df = build_schedule(urls)
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            message=str(e),
            error=True,
            urls_value=urls_raw,
            profile_url=profile_url,
            schedule=None,
            team_choices=None,
            current_year=current_year,
            filtered_to_year=False,
        )

    schedule = out_df.to_dict(orient='records')

    return render_template_string(
        HTML_TEMPLATE,
        message=None,
        error=False,
        urls_value=urls_raw,
        profile_url=profile_url,
        schedule=schedule,
        team_choices=None,
        current_year=current_year,
        filtered_to_year=False,
    )


@app.route('/download', methods=['POST'])
def download():
    urls_raw = request.form.get('urls', '')
    profile_url = request.form.get('profile_url', '').strip()
    current_year = datetime.now().year

    urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
    if not urls:
        return render_template_string(
            HTML_TEMPLATE,
            message="Please generate a schedule first.",
            error=True,
            urls_value=urls_raw,
            profile_url=profile_url,
            schedule=None,
            team_choices=None,
            current_year=current_year,
            filtered_to_year=False,
        )

    try:
        out_df = build_schedule(urls)
    except Exception as e:
        return render_template_string(
            HTML_TEMPLATE,
            message=str(e),
            error=True,
            urls_value=urls_raw,
            profile_url=profile_url,
            schedule=None,
            team_choices=None,
            current_year=current_year,
            filtered_to_year=False,
        )

    # Write to in-memory Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        out_df[['Date', 'Team name', 'Match time', 'All start times / lanes', 'Opponent team', 'Home/Away']].to_excel(writer, index=False, sheet_name='Schedule')
        wb = writer.book
        ws = writer.sheets['Schedule']

        from openpyxl.styles import PatternFill, Font

        # Make header row bold
        header_font = Font(bold=True)
        for col in range(1, ws.max_column + 1):
            ws.cell(row=1, column=col).font = header_font

        # Format date column as "mmm d"
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=1)
            if isinstance(cell.value, datetime):
                cell.number_format = 'mmm d'

        # Highlight conflicts by date only
        groups = {}
        for row in range(2, ws.max_row + 1):
            date_val = ws.cell(row=row, column=1).value
            if not date_val:
                continue
            groups.setdefault(date_val, []).append(row)

        conflict_rows = {r for rows in groups.values() if len(rows) > 1 for r in rows}
        highlight_fill = PatternFill(start_color='FFFF99', end_color='FFFF99', fill_type='solid')
        for row in conflict_rows:
            for col in range(1, ws.max_column + 1):
                ws.cell(row=row, column=col).fill = highlight_fill

    output.seek(0)
    filename = 'usta_schedule_combined.xlsx'
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == '__main__':
    app.run(debug=True)
