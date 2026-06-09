const API_BASE = 'https://your-api.railway.app';

export async function apiRequest(method, path, body = null) {
  const token = await getStoredToken();
  const options = { method, headers: { 'Content-Type': 'application/json' } };
  if (token) options.headers['Authorization'] = `Bearer ${token}`;
  if (body) options.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

function getStoredToken() {
  return new Promise((resolve) =>
    chrome.storage.local.get('jwt_token', (d) => resolve(d.jwt_token || null))
  );
}

export const api = {
  get: (path) => apiRequest('GET', path),
  post: (path, body) => apiRequest('POST', path, body),
  patch: (path, body) => apiRequest('PATCH', path, body),
  delete: (path) => apiRequest('DELETE', path)
};
