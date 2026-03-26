from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify, send_file

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>USTA NorCal League Tools</title>
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
    .features-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; margin: 0 auto; max-width: 800px; }
    .feature { text-align: center; padding: 1.5rem; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .feature h3 { margin: 0 0 1rem 0; font-size: 1.3rem; color: #01696f; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
    .feature p { margin: 0; font-size: 1rem; line-height: 1.5; color: #333; text-align: center; }
    .app-buttons { display: flex; gap: 1.5rem; justify-content: center; margin-top: 3rem; }
    .app-button { background-color: #01696f; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 1rem; min-width: 200px; transition: background-color 0.3s; }
    .app-button:hover { background-color: #014e54; }
    .app-button.stats { background-color: #2e7d32; }
    .app-button.stats:hover { background-color: #1b5e20; }
    .app-container { border: 2px solid #ddd; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; background: white; }
    .clear-button { background-color: #a12c2c; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: var(--tennis-cursor) !important; font-weight: 600; margin-top: 2rem; }
    .clear-button:hover { background-color: #8b1f1f; }
    .hidden { display: none; }
    .app-section { margin-top: 3rem; }
    label { font-weight: 600; display: block; margin-bottom: 0.25rem; }
    .radio-label { font-weight: 400; display: inline-block; margin-bottom: 0; margin-right: 1rem; }
    input[type="radio"] { margin-right: 0.5rem; width: auto; padding: 0; }
    input, select, textarea { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px; }
    button { background-color: #01696f; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: var(--tennis-cursor) !important; font-weight: 600; }
    button:hover { background-color: #014e54; }
    .app-button { cursor: var(--tennis-cursor); }
    .clear-button { cursor: var(--tennis-cursor); }
    .status { margin-top: 1rem; padding: 0.75rem; border-radius: 4px; }
    .error { background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
    .success { background-color: #e8f5e8; color: #2e7d32; border: 1px solid #c8e6c9; }
    .results { margin-top: 2rem; }
    .schedule-table, .stats-table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
    .schedule-table th, .schedule-table td, .stats-table th, .stats-table td { border: 1px solid #ddd; padding: 0.5rem; text-align: left; }
    .schedule-table th, .stats-table th { background-color: #01696f; color: white; font-weight: 600; }
    .schedule-table tr:nth-child(even), .stats-table tr:nth-child(even) { background-color: #f9f9f9; }
    .schedule-table .conflict-row { background-color: #fff7c2; }
    .schedule-table .pending { color: #9a9a9a; font-style: italic; }
    tr.conflict { background: #fff7c2; }
    tr.conflict td { color: #222; }
    tr.pending { background: #efefef; color: #9a9a9a; font-style: italic; }
    tr.conflict.pending { background: #efefef !important; color: #9a9a9a !important; font-style: italic; }
    tr.pending td { color: #9a9a9a !important; font-style: italic !important; }
    tr.conflict.pending td { color: #9a9a9a !important; font-style: italic !important; }
    .footnote-link { margin-left: 0.25rem; color: #01696f; font-weight: 900; text-decoration: none; }
    .footnote-link:hover { text-decoration: underline; }
    #schedule-results .team-list label,
    #stats-results .team-list label { display: flex !important; align-items: center !important; font-weight: 400 !important; gap: 0.5rem; }
    #schedule-results input[type="checkbox"],
    #stats-results input[type="checkbox"] { width: auto !important; margin: 0 !important; padding: 0 !important; flex-shrink: 0; }
    #schedule-results .team-list,
    #stats-results .team-list { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
    #schedule-results button,
    #stats-results button { background-color: #01696f; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: var(--tennis-cursor) !important; font-weight: 600; margin-top: 1rem; }
    #schedule-results button:hover,
    #stats-results button:hover { background-color: #014e54; }
    #schedule-results .clear-button,
    #stats-results .clear-button { background-color: #a12c2c !important; }
    #schedule-results .clear-button:hover,
    #stats-results .clear-button:hover { background-color: #8b1f1f !important; }
    .stats-table .grand-total { background-color: #e8f4f8; font-weight: bold; }
    .stats-table .grand-total td { border-top: 2px solid #01696f; }
    .help { font-size: 0.9rem; color: #666; margin-top: -0.5rem; margin-bottom: 1rem; }
    .team-list { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
    .team-list label { font-weight: 400; }
    fieldset { border: 1px solid #ddd; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; }
    legend { padding: 0 0.25rem; font-weight: 600; }
    td.homeaway_home { color: #01696f !important; font-weight: 700; }
    td.homeaway_away { color: #a12c2c !important; font-weight: 700; }
    td.location_home { color: #0b6b0b !important; font-weight: 600; }
    td.location_away { color: #6b2d91 !important; font-weight: 600; }
    .actions { margin-top: 1rem; }
    /* Universal rule to ensure all buttons get tennis cursor, overriding sub-app styles */
    button, .app-button, .clear-button, input[type="submit"] { cursor: var(--tennis-cursor) !important; }
  </style>
</head>
<body>
  <div id="landing-page" class="landing">
    <h1>USTA NorCal League Tools</h1>
    <div class="intro">
      <div class="intro-header">
        <p>Two essential tools for tennis players and team captains</p>
      </div>
      <div class="features-grid">
        <div class="feature">
          <h3>📅 Schedule Organizer</h3>
          <p>Combine league schedule across teams with match-day overlap detection.</p>
        </div>
        <div class="feature">
          <h3>📊 Player Statistics</h3>
          <p>Extract comprehensive USTA league career stats.</p>
        </div>
      </div>
      <div class="app-buttons">
        <button class="app-button" onclick="toggleApp('schedule')">Schedule Organizer</button>
        <button class="app-button stats" onclick="toggleApp('stats')">Player Statistics</button>
      </div>
    </div>
  </div>

  <!-- Schedule app landing -->
  <div id="schedule-section" class="app-section hidden">
    <div id="schedule-landing" class="app-container">
      <h2>Schedule Organizer</h2>
      <p>Step 1: Choose whether to use your USTA NorCal player profile or paste individual team info URLs.</p>
      <p>Step 2: Review the combined schedule and download an Excel file with conflicts highlighted.</p>
      <form id="schedule-form" method="post" action="/generate">
        <fieldset>
          <legend>Step 1: Input method</legend>
          <div>
            <label class="radio-label">
              <input type="radio" name="mode" value="profile" onchange="toggleMode()" checked> Profile URL (auto-discover teams)
            </label>
            <label class="radio-label">
              <input type="radio" name="mode" value="teams" onchange="toggleMode()"> Manual team URLs
            </label>
          </div>
        </fieldset>
        <div id="profile-input">
          <label for="profile_url">Player profile URL</label>
          <input type="url" id="profile_url" name="profile_url" placeholder="https://leagues.ustanorcal.com/...playermatches.asp?id=...">
          <div class="help">Enter your USTA NorCal player profile URL to auto-discover teams.</div>
        </div>
        <div id="teams-input" class="hidden">
          <label for="urls">Team info URLs (one per line)</label>
          <textarea id="urls" name="urls" rows="6" placeholder="https://leagues.ustanorcal.com/...teaminfo.asp?id=..."></textarea>
        </div>
        <button type="submit">Analyze</button>
      </form>
      <button class="clear-button" onclick="clearAll()">Go Back</button>
    </div>
  </div>

  <!-- Schedule results (loaded via AJAX) -->
  <div id="schedule-results" class="app-section hidden"></div>

  <!-- Stats app landing -->
  <div id="stats-section" class="app-section hidden">
    <div id="stats-landing" class="app-container">
      <h2>Player Statistics</h2>
      <p>View comprehensive career statistics extracted from your USTA NorCal player profile.</p>
      <form id="stats-form" method="post" action="/analyze">
        <label for="profile_url_stats">Player profile URL</label>
        <input type="url" id="profile_url_stats" name="profile_url" placeholder="https://leagues.ustanorcal.com/...playermatches.asp?id=..." required>
        <div class="help">Enter your USTA NorCal player profile URL to extract career statistics.</div>
        <button type="submit">Analyze</button>
      </form>
      <button class="clear-button" onclick="clearAll()">Go Back</button>
    </div>
  </div>

  <!-- Stats results (loaded via AJAX) -->
  <div id="stats-results" class="app-section hidden"></div>

  <script>
    function toggleApp(appType) {
      clearAll();
      if (appType === 'schedule') {
        document.getElementById('schedule-section').classList.remove('hidden');
        setTimeout(function() {
          document.getElementById('schedule-section').scrollIntoView({ behavior: 'smooth' });
        }, 100);
      } else if (appType === 'stats') {
        document.getElementById('stats-section').classList.remove('hidden');
        setTimeout(function() {
          document.getElementById('stats-section').scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    }

    function clearAll() {
      document.getElementById('schedule-section').classList.add('hidden');
      document.getElementById('schedule-results').classList.add('hidden');
      document.getElementById('schedule-results').innerHTML = '';
      document.getElementById('stats-section').classList.add('hidden');
      document.getElementById('stats-results').classList.add('hidden');
      document.getElementById('stats-results').innerHTML = '';
      
      // Show Go Back buttons when results are cleared
      showGoBackButtons();
      
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function hideGoBackButtons() {
      // Hide Go Back buttons on landing pages when results are shown
      const scheduleGoBack = document.querySelector('#schedule-landing .clear-button');
      const statsGoBack = document.querySelector('#stats-landing .clear-button');
      if (scheduleGoBack) scheduleGoBack.style.display = 'none';
      if (statsGoBack) statsGoBack.style.display = 'none';
    }

    function showGoBackButtons() {
      // Show Go Back buttons when results are cleared
      const scheduleGoBack = document.querySelector('#schedule-landing .clear-button');
      const statsGoBack = document.querySelector('#stats-landing .clear-button');
      if (scheduleGoBack) scheduleGoBack.style.display = 'block';
      if (statsGoBack) statsGoBack.style.display = 'block';
    }

    function submitFormAjax(form, resultsId) {
      var formData = new FormData(form);
      fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
      })
      .then(function(response) { return response.text(); })
      .then(function(html) {
        var container = document.getElementById(resultsId);
        container.innerHTML = html;
        container.classList.remove('hidden');
        
        // Hide Go Back buttons when results are loaded
        hideGoBackButtons();
        
        setTimeout(function() {
          container.scrollIntoView({ behavior: 'smooth' });
        }, 100);
        // Re-attach submit handlers to any new forms inside results
        attachResultFormHandlers();
      })
      .catch(function(err) {
        console.error('Error:', err);
        alert('Error: ' + err.message);
      });
    }

    function attachResultFormHandlers() {
      // Attach handlers to forms loaded via AJAX inside results
      var forms = document.querySelectorAll('#schedule-results form, #stats-results form');
      forms.forEach(function(form) {
        if (!form.dataset.bound) {
          form.dataset.bound = 'true';
          var resultsId = form.closest('#schedule-results') ? 'schedule-results' : 'stats-results';
          form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormAjax(form, resultsId);
          });
        }
      });
    }

    function toggleMode() {
      var mode = document.querySelector('input[name="mode"]:checked').value;
      var profileInput = document.getElementById('profile-input');
      var teamsInput = document.getElementById('teams-input');
      if (mode === 'profile') {
        profileInput.classList.remove('hidden');
        teamsInput.classList.add('hidden');
      } else {
        profileInput.classList.add('hidden');
        teamsInput.classList.remove('hidden');
      }
    }

    document.addEventListener('DOMContentLoaded', function() {
      toggleMode();

      document.getElementById('schedule-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitFormAjax(this, 'schedule-results');
      });

      document.getElementById('stats-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitFormAjax(this, 'stats-results');
      });
    });
  </script>
</body>
</html>
"""
# ---------------------------------------------------------------------------
import importlib.util, sys

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        sys.modules[name] = mod
        return mod
    except Exception as e:
        print(f"Error loading {name}: {e}")
        return None

schedule_module = _load_module("schedule_app", "app_schedule.py")
stats_module    = _load_module("stats_app",    "app_stat.py")


def _extract_results_only(html_string):
    """Strip the repeated header / intro / input-form from the original
    app's full-page HTML.  Return only the results portion (team selection,
    schedule table, stats tables, status messages) wrapped in an
    app-container box with a Clear button.  Preserves the original app's
    CSS so that conflict highlighting, homeaway colours etc. still work."""
    soup = BeautifulSoup(html_string, 'html.parser')

    body = soup.find('body')
    if not body:
        return html_string

    # Remove repeated elements already shown in our landing page
    h1 = body.find('h1')
    if h1:
        h1.decompose()

    first_form = body.find('form')
    if first_form:
        for sibling in list(first_form.previous_siblings):
            if hasattr(sibling, 'name') and sibling.name == 'p':
                sibling.decompose()
        first_form.decompose()

    for script in body.find_all('script'):
        script.decompose()

    inner = body.decode_contents().strip()

    return ('<div class="app-container">\n'
            + inner
            + '\n<button class="clear-button" onclick="clearAll()">Clear</button>'
            + '\n</div>')


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/generate', methods=['POST'])
def generate():
    if not schedule_module:
        return '<div class="status error">Schedule app module not available.</div>'

    result = schedule_module.schedule_generate()

    # File download (e.g. Excel) — pass through
    if hasattr(result, 'status_code'):
        return result

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if isinstance(result, str):
        if is_ajax:
            return _extract_results_only(result)
        return result

    # dict result (shouldn't normally happen but handle gracefully)
    if isinstance(result, dict):
        return render_template_string(HTML_TEMPLATE, **result)

    return result


@app.route('/download', methods=['POST'])
def download():
    if schedule_module:
        return schedule_module.schedule_download()
    return 'Schedule app module not available.'


@app.route('/analyze', methods=['POST'])
def analyze():
    if not stats_module:
        return '<div class="status error">Statistics app module not available.</div>'

    result = stats_module.stats_analyze()

    if hasattr(result, 'status_code'):
        return result

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if isinstance(result, str):
        if is_ajax:
            return _extract_results_only(result)
        return result

    if isinstance(result, dict):
        return render_template_string(HTML_TEMPLATE, **result)

    return result


if __name__ == '__main__':
    app.run(debug=True, port=5000)
