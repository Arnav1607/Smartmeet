const MEETING_PATTERNS = {
  gmeet: /^https:\/\/meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}/,
  zoom:  /^https:\/\/.*\.zoom\.us\/j\//,
  teams: /^https:\/\/teams\.microsoft\.com\//
};

function detectPlatform(url) {
  for (const [platform, pattern] of Object.entries(MEETING_PATTERNS)) {
    if (pattern.test(url)) return platform;
  }
  return null;
}

// Track active meetings per tab
const activeMeetings = {};

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== 'complete' || !tab.url) return;
  const platform = detectPlatform(tab.url);

  if (platform && !activeMeetings[tabId]) {
    activeMeetings[tabId] = { platform, url: tab.url, startedAt: Date.now() };
    chrome.notifications.create(`meeting-start-${tabId}`, {
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'SmartMeet AI — Recording',
      message: `${platform.toUpperCase()} meeting detected. Transcript capture started.`
    });
    // Notify content script
    chrome.tabs.sendMessage(tabId, { type: 'MEETING_STARTED', platform });
  }

  if (!platform && activeMeetings[tabId]) {
    chrome.tabs.sendMessage(tabId, { type: 'MEETING_ENDED' });
    delete activeMeetings[tabId];
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (activeMeetings[tabId]) {
    delete activeMeetings[tabId];
  }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_AUTH_TOKEN') {
    chrome.storage.local.get('jwt_token', (data) => {
      sendResponse({ token: data.jwt_token || null });
    });
    return true; // async
  }
  if (msg.type === 'SET_AUTH_TOKEN') {
    chrome.storage.local.set({ jwt_token: msg.token }, () => sendResponse({ ok: true }));
    return true;
  }
  if (msg.type === 'CLEAR_AUTH_TOKEN') {
    chrome.storage.local.remove('jwt_token', () => sendResponse({ ok: true }));
    return true;
  }
});
