export function saveToken(token) {
  return new Promise((resolve) => chrome.storage.local.set({ jwt_token: token }, resolve));
}
export function getToken() {
  return new Promise((resolve) => chrome.storage.local.get('jwt_token', (d) => resolve(d.jwt_token || null)));
}
export function clearToken() {
  return new Promise((resolve) => chrome.storage.local.remove('jwt_token', resolve));
}
export function isTokenExpired(token) {
  if (!token) return true;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch { return true; }
}
