"""Dashboard HTML generation."""
from __future__ import annotations


def get_html() -> str:
    """Return the full dashboard HTML page."""
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Syx LLM Overlord</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@300;400;600&display=swap');

  :root {
    --bg-dark: #0a0a0f;
    --bg-panel: #12121a;
    --bg-card: #1a1a28;
    --border: #2a2a3a;
    --text: #c8c8d0;
    --text-dim: #666680;
    --text-bright: #e8e8f0;
    --gold: #d4a843;
    --gold-dim: #8a6b20;
    --red: #c44040;
    --green: #40a040;
    --blue: #4080c0;
    --purple: #8060c0;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg-dark);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    overflow: hidden;
    height: 100vh;
  }

  header {
    background: linear-gradient(180deg, #18182a 0%, var(--bg-dark) 100%);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  header h1 {
    font-family: 'Cinzel', serif;
    font-size: 22px;
    color: var(--gold);
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  header .status {
    display: flex;
    gap: 16px;
    align-items: center;
    font-size: 12px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 4px;
  }

  .status-dot.online { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .status-dot.offline { background: var(--red); box-shadow: 0 0 6px var(--red); }

  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr;
    gap: 1px;
    height: calc(100vh - 52px);
    background: var(--border);
  }

  .panel {
    background: var(--bg-panel);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .panel-header {
    padding: 10px 16px;
    font-family: 'Cinzel', serif;
    font-size: 13px;
    color: var(--gold);
    border-bottom: 1px solid var(--border);
    text-transform: uppercase;
    letter-spacing: 1px;
    flex-shrink: 0;
  }

  .panel-body {
    padding: 12px 16px;
    overflow-y: auto;
    flex: 1;
  }

  /* State panel */
  .stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 10px 12px;
  }

  .stat-label {
    font-size: 10px;
    text-transform: uppercase;
    color: var(--text-dim);
    letter-spacing: 1px;
    margin-bottom: 4px;
  }

  .stat-value {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-bright);
  }

  /* LLM Thoughts */
  .thought-bubble {
    background: var(--bg-card);
    border-left: 3px solid var(--purple);
    padding: 12px 16px;
    margin-bottom: 10px;
    border-radius: 0 4px 4px 0;
    animation: fadeIn 0.3s ease;
  }

  .thought-mood {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }

  .mood-confident { color: var(--gold); }
  .mood-cautious { color: var(--blue); }
  .mood-aggressive { color: var(--red); }
  .mood-worried { color: #c08040; }
  .mood-pleased { color: var(--green); }
  .mood-frustrated { color: var(--red); }
  .mood-neutral { color: var(--text-dim); }

  .thought-text {
    font-size: 13px;
    line-height: 1.5;
    color: var(--text);
  }

  /* Command history */
  .command-entry {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    padding: 6px 0;
    border-bottom: 1px solid #1a1a2a;
    animation: fadeIn 0.2s ease;
  }

  .command-tick {
    color: var(--text-dim);
    font-size: 11px;
    min-width: 40px;
    font-family: monospace;
  }

  .command-action {
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 12px;
    font-family: monospace;
  }

  .command-result {
    font-size: 11px;
  }

  .command-result.ok { color: var(--green); }
  .command-result.fail { color: var(--red); }

  /* Resources */
  .resource-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .resource-name {
    font-size: 12px;
    min-width: 100px;
    color: var(--text-dim);
  }

  .resource-fill {
    flex: 1;
    height: 6px;
    background: var(--bg-dark);
    border-radius: 3px;
    overflow: hidden;
  }

  .resource-fill-inner {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
  }

  .resource-count {
    font-size: 12px;
    font-family: monospace;
    min-width: 50px;
    text-align: right;
  }

  /* Connection overlay */
  .overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 10, 15, 0.95);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }

  .overlay.hidden { display: none; }

  .overlay h2 {
    font-family: 'Cinzel', serif;
    color: var(--gold);
    font-size: 24px;
    margin-bottom: 12px;
  }

  .overlay p {
    color: var(--text-dim);
    font-size: 14px;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .thinking { animation: pulse 1.5s infinite; }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg-dark); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<header>
  <h1>Syx LLM Overlord</h1>
  <div class="status">
    <span><span class="status-dot" id="gameStatus"></span> Game</span>
    <span><span class="status-dot" id="llmStatus"></span> LLM</span>
    <span id="tickCounter" style="color: var(--text-dim); font-family: monospace;">Tick: --</span>
  </div>
</header>

<div class="grid">
  <!-- Top Left: Game State -->
  <div class="panel">
    <div class="panel-header">Kingdom Status</div>
    <div class="panel-body" id="statePanel">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-label">Population</div>
          <div class="stat-value" id="statPop">--</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Day / Year</div>
          <div class="stat-value" id="statTime">--</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Happiness</div>
          <div class="stat-value" id="statHappy">--</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Military</div>
          <div class="stat-value" id="statMilitary">--</div>
        </div>
      </div>
      <div style="margin-top: 16px;">
        <div class="stat-label" style="margin-bottom: 8px;">Resources</div>
        <div id="resourcesList"></div>
      </div>
    </div>
  </div>

  <!-- Top Right: LLM Thoughts -->
  <div class="panel">
    <div class="panel-header">LLM Deliberations</div>
    <div class="panel-body" id="thoughtsPanel">
      <div style="color: var(--text-dim); text-align: center; margin-top: 40px;">
        Awaiting first decision...
      </div>
    </div>
  </div>

  <!-- Bottom: Command History (spans both columns) -->
  <div class="panel" style="grid-column: 1 / -1;">
    <div class="panel-header">Command Chronicle</div>
    <div class="panel-body" id="historyPanel">
      <div style="color: var(--text-dim); text-align: center;">
        No commands yet
      </div>
    </div>
  </div>
</div>

<div class="overlay" id="overlay">
  <h2>Waiting for Connection</h2>
  <p class="thinking">Attempting to reach the Syx LLM Overlord bridge...</p>
</div>

<script>
const WS_URL = `ws://${location.host}/ws`;
let ws = null;
let reconnectTimer = null;
let tickCount = 0;

function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    document.getElementById('overlay').classList.add('hidden');
    document.getElementById('llmStatus').className = 'status-dot online';
    document.getElementById('gameStatus').className = 'status-dot online';
    console.log('Connected to bridge');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
  };

  ws.onclose = () => {
    document.getElementById('overlay').classList.remove('hidden');
    document.getElementById('llmStatus').className = 'status-dot offline';
    document.getElementById('gameStatus').className = 'status-dot offline';
    reconnectTimer = setTimeout(connect, 3000);
  };

  ws.onerror = () => ws.close();
}

function handleMessage(data) {
  if (data.type === 'tick') {
    tickCount = data.tick;
    document.getElementById('tickCounter').textContent = `Tick: ${tickCount}`;
    updateState(data.state);
    updateThoughts(data.decision);
    updateHistory(data.tick, data.decision, data.results);
  } else if (data.type === 'state') {
    updateState(data.state);
  } else if (data.type === 'error') {
    document.getElementById('gameStatus').className = 'status-dot offline';
  }
}

function updateState(state) {
  if (!state) return;
  document.getElementById('gameStatus').className = 'status-dot online';

  // Population
  const pop = state.population?.total;
  document.getElementById('statPop').textContent = pop != null ? pop.toLocaleString() : '--';

  // Time
  const day = state.gameTime?.day;
  const year = state.gameTime?.year;
  document.getElementById('statTime').textContent =
    (day != null && year != null) ? `${day} / ${year}` : '--';

  // Happiness
  const happy = state.happiness?.overall;
  document.getElementById('statHappy').textContent =
    happy != null ? `${(happy * 100).toFixed(0)}%` : '--';

  // Military
  const mil = state.military?.divisions;
  document.getElementById('statMilitary').textContent = mil != null ? `${mil} div` : '--';

  // Resources
  const resDiv = document.getElementById('resourcesList');
  if (state.resources && Object.keys(state.resources).length > 0) {
    const entries = Object.entries(state.resources).slice(0, 15);
    const maxVal = Math.max(...entries.map(([_, v]) => Number(v) || 1));
    resDiv.innerHTML = entries.map(([name, val]) => {
      const pct = Math.min(100, (Number(val) / maxVal) * 100);
      const color = pct > 60 ? 'var(--green)' : pct > 30 ? 'var(--gold)' : 'var(--red)';
      return `<div class="resource-bar">
        <span class="resource-name">${name}</span>
        <div class="resource-fill"><div class="resource-fill-inner" style="width:${pct}%;background:${color}"></div></div>
        <span class="resource-count">${Number(val).toLocaleString()}</span>
      </div>`;
    }).join('');
  }
}

function updateThoughts(decision) {
  if (!decision) return;
  const panel = document.getElementById('thoughtsPanel');
  const moodClass = `mood-${decision.mood || 'neutral'}`;
  const cmdCount = (decision.commands || []).length;

  const html = `<div class="thought-bubble">
    <div class="thought-mood ${moodClass}">
      ${decision.mood || 'neutral'} -- ${cmdCount} command${cmdCount !== 1 ? 's' : ''} issued
    </div>
    <div class="thought-text">${decision.reasoning || 'No reasoning provided'}</div>
  </div>` + panel.innerHTML;

  // Keep only last 20 thoughts
  panel.innerHTML = html.substring(0, 8000);
}

function updateHistory(tick, decision, results) {
  const panel = document.getElementById('historyPanel');
  const commands = decision?.commands || [];
  if (commands.length === 0) return;

  let html = '';
  commands.forEach((cmd, i) => {
    const res = results?.[i];
    const ok = res?.success;
    const msg = res?.message || '';
    html += `<div class="command-entry">
      <span class="command-tick">#${tick}</span>
      <span class="command-action">${cmd.action}${cmd.target ? ' ' + cmd.target : ''}</span>
      <span class="command-result ${ok ? 'ok' : 'fail'}">${ok ? '&#10003;' : '&#10007;'} ${msg}</span>
    </div>`;
  });

  panel.innerHTML = html + panel.innerHTML;
  // Keep last 100 entries
  if (panel.children.length > 100) {
    panel.innerHTML = Array.from(panel.children).slice(0, 100).map(e => e.outerHTML).join('');
  }
}

connect();
</script>
</body>
</html>
"""
