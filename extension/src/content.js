const API_BASE = 'http://localhost:5000'; // Target local port for seamless evaluation

const SELECTORS = {
  gmeet: {
    captionContainer: '[data-message-text]',
    speaker: '[data-sender-name]',
    rootObserveTarget: 'body'
  },
  zoom: {
    captionContainer: '.caption-line',
    speaker: '.speakername',
    rootObserveTarget: '.caption-container'
  },
  teams: {
    captionContainer: '.ts-message-renderWrapper',
    speaker: '.author',
    rootObserveTarget: '.ts-messages-container'
  }
};

let platform = null;
let meetingId = null;
let buffer = [];
let flushInterval = null;
let observer = null;

function generateId() {
  return 'mtg_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
}

async function getToken() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: 'GET_AUTH_TOKEN' }, (res) => {
      resolve(res?.token || null);
    });
  });
}

async function apiPost(path, body) {
  const token = await getToken();
  if (!token) { console.warn('[SmartMeet] Not logged in'); return; }
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    return res.ok ? await res.json() : null;
  } catch (e) {
    console.error('[SmartMeet] API error:', e);
  }
}

function parseCaptionNode(node, sel) {
  const speakerEl = node.querySelector(sel.speaker) || node.previousElementSibling?.querySelector(sel.speaker);
  const speaker = speakerEl?.textContent?.trim() || 'Unknown';
  const text = node.textContent?.trim();
  if (!text || text.length < 2) return null;
  return { speaker, text, ts: Date.now() };
}

async function startCapture(plt) {
  platform = plt;
  meetingId = generateId();
  const sel = SELECTORS[platform];
  if (!sel) return;

  // Register meeting on backend
  await apiPost('/api/meetings/start', {
    meetingId,
    platform,
    title: document.title,
    startedAt: new Date().toISOString()
  });

  const target = document.querySelector(sel.rootObserveTarget) || document.body;
  observer = new MutationObserver((mutations) => {
    mutations.forEach((m) => {
      m.addedNodes.forEach((node) => {
        if (node.nodeType !== 1) return;
        const matches = node.matches?.(sel.captionContainer)
          ? [node]
          : [...node.querySelectorAll(sel.captionContainer)];
        matches.forEach((el) => {
          const entry = parseCaptionNode(el, sel);
          if (entry) buffer.push(entry);
        });
      });
    });
  });

  observer.observe(target, { childList: true, subtree: true });

  // Flush every 30 seconds
  flushInterval = setInterval(flushBuffer, 30000);
  console.log(`[SmartMeet] Capture started on ${platform}, meetingId: ${meetingId}`);
}

async function flushBuffer() {
  if (buffer.length === 0) return;
  const entries = [...buffer];
  buffer = [];
  await apiPost('/api/transcript/append', { meetingId, platform, entries });
}

async function endCapture() {
  clearInterval(flushInterval);
  if (observer) observer.disconnect();
  await flushBuffer(); // flush remaining
  await apiPost(`/api/meetings/${meetingId}/end`, { endedAt: new Date().toISOString() });
  console.log('[SmartMeet] Capture ended, processing triggered.');
}

// Listen for messages from background.js
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'MEETING_STARTED') startCapture(msg.platform);
  if (msg.type === 'MEETING_ENDED') endCapture();
});
