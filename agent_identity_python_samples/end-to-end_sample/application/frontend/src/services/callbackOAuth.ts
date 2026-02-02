export default async function callbackOAuth({ authorizeCode, state }: {
  authorizeCode: string;
  state: string;
}): Promise<{ sessionId: string; }> {
  const response = await fetch('/callback_for_oauth', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code: authorizeCode,
      state
    }),
  });

  if (!response.ok) {
    throw new Error(`callbakc_for_oauth error! status: ${response.status}`);
  }

  const data = await response.json();

  return {
    sessionId: data.session_id
  }
};