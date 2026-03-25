from flask import Flask, request, send_file, render_template_string
import io
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>USTA Team Schedule Combiner</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; background: #f7f6f2; color: #222; }
    h1 { font-size: 1.75rem; margin-bottom: 1rem; }
    label { font-weight: 600; display: block; margin-bottom: 0.25rem; }
    textarea { width: 100%; min-height: 140px; padding: 0.75rem; border-radius: 8px; border: 1px solid #ccc; font-family: monospace; font-size: 0.9rem; }
    button { margin-top: 1rem; padding: 0.75rem 1.25rem; border-radius: 999px; border: none; background: #01696f; color: #fff; font-weight: 600; cursor: pointer; }
    button:hover { background: #0c4e54; }
    .help { font-size: 0.85rem; color: #666; margin-top: 0.25rem; }
    .status { margin-top: 1rem; font-size: 0.9rem; color: #444; }
    .error { color: #a12c2c; }
    .example { font-size: 0.85rem; margin-top: 0.5rem; }
    code { background: #f0efea; padding: 0.1rem 0.3rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>USTA Team Schedule Combiner</h1>
  <p>Paste one or more USTA NorCal team info page URLs (one per line). The app will fetch each schedule and generate a combined Excel file with conflicts highlighted.</p>
  <form method="post" action="/generate">
    <label for="urls">Team info URLs</label>
    <textarea id="urls" name="urls" placeholder="https://leagues.ustanorcal.com/teaminfo.asp?id=109510
https://leagues.ustanorcal.com/teaminfo.asp?id=109621"></textarea>
    <div class="help">Use the full <code>teaminfo.asp?id=...</code> links. You can paste as many as you want.</div>
    <button type="submit">Generate Excel Schedule</button>
  </form>
  {% if message %}
  <div class="status {% if error %}error{% endif %}">{{ message }}</div>
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


@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/generate', methods=['POST'])
def generate():
    urls_raw = request.form.get('urls', '')
    urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
    if not urls:
        return render_template_string(HTML_TEMPLATE, message="Please paste at least one URL.", error=True)

    all_rows = []
    for url in urls:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, message=f"Error fetching {url}: {e}", error=True)

        fallback_name = url
        rows = parse_schedule_html(resp.text, fallback_name)
        if not rows:
            return render_template_string(HTML_TEMPLATE, message=f"Could not find a schedule table on {url}.", error=True)
        all_rows.extend(rows)

    if not all_rows:
        return render_template_string(HTML_TEMPLATE, message="No matches found in the provided pages.", error=True)

    df = pd.DataFrame(all_rows)
    df['Date'] = pd.to_datetime(df['Date_raw'], format='%m/%d/%y', errors='coerce')
    df = df.sort_values(by=['Date', 'Match time', 'Team name']).reset_index(drop=True)

    out_df = df[['Date', 'Team name', 'Match time', 'All start times / lanes', 'Opponent team', 'Home/Away']].copy()

    # Write to in-memory Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        out_df.to_excel(writer, index=False, sheet_name='Schedule')
        wb = writer.book
        ws = writer.sheets['Schedule']

        # Format date column as "mmm d"
        from openpyxl.styles import PatternFill
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
