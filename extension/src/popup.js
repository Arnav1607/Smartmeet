const API_BASE = 'http://localhost:5000';
const DASHBOARD_URL = 'http://localhost:5173';

async function getToken() {
  return new Promise(resolve => chrome.storage.local.get('jwt_token', d => resolve(d.jwt_token || null)));
}

async function login() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const errEl = document.getElementById('login-error');
  if (!email || !password) { showError('Please fill all fields'); return; }

  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) { showError(data.error || 'Login failed'); return; }
    chrome.storage.local.set({ jwt_token: data.token }, () => {
      errEl.style.display = 'none';
      showLoggedIn();
      loadStats();
    });
  } catch {
    showError('Cannot reach server. Check connection.');
  }
}

function showError(msg) {
  const el = document.getElementById('login-error');
  el.textContent = msg;
  el.style.display = 'block';
}

function showLoggedIn() {
  document.getElementById('login-view').style.display = 'none';
  document.getElementById('logged-in-view').style.display = 'block';
}

function logout() {
  chrome.storage.local.remove('jwt_token', () => {
    document.getElementById('login-view').style.display = 'block';
    document.getElementById('logged-in-view').style.display = 'none';
  });
}

function openDashboard() {
  chrome.tabs.create({ url: DASHBOARD_URL });
}

async function loadStats() {
  const token = await getToken();
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/api/dashboard/stats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    document.getElementById('stat-total').textContent = data.total_meetings || 0;
    document.getElementById('stat-hours').textContent = data.total_hours || 0;
    document.getElementById('stat-tasks').textContent = data.pending_tasks || 0;
  } catch {}
}

// Check active meeting in current tab
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const url = tabs[0]?.url || '';
  const isMeeting = /meet\.google\.com|zoom\.us\/j|teams\.microsoft\.com/.test(url);
  if (isMeeting) {
    document.getElementById('status-dot').className = 'status-dot recording';
    document.getElementById('status-text').textContent = 'Recording in progress';
    document.getElementById('recording-info').style.display = 'block';
    document.getElementById('meeting-title').textContent = tabs[0].title || 'Meeting';
    const platform = url.includes('meet.google') ? 'Google Meet'
      : url.includes('zoom') ? 'Zoom' : 'Teams';
    document.getElementById('meeting-platform').textContent = platform;
  } else {
    document.getElementById('status-dot').className = 'status-dot';
    document.getElementById('status-text').textContent = 'No meeting detected';
  }
});

// Init
getToken().then(token => {
  if (token) { showLoggedIn(); loadStats(); }
});
