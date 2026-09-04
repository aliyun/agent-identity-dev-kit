export default async function callbackOAuth(): Promise<string> {
  const response = await fetch('/auth', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    }
  });

  if (!response.ok) {
    throw new Error(`oauth error! status: ${response.status}`);
  }

  const data = await response.json();

  return data
};