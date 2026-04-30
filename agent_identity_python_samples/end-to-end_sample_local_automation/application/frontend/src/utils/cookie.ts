export const getSessionId = () => {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('oauthSessionId='))
    ?.split('=')[1] || '';
};

export const setSessionId = (sessionId: string, days = 1) => {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `oauthSessionId=${sessionId}; expires=${expires}; path=/`;
};

export const clearSessionId = () => {
  document.cookie = "oauthSessionId=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
};