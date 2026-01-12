export default async function chat({ input, chat_sessionId, oauth_sessionId }: {
  input: string;
  oauth_sessionId: string;
  chat_sessionId: string;
}) {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'SESSION-ID': oauth_sessionId
    },
    body: JSON.stringify({
      session_id: chat_sessionId,
      input: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: input,
              user_id: 'seeq',
            },
          ],
        },
      ],
    })
  });

  if (response.status !== 200 || !response.body) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.body;
};