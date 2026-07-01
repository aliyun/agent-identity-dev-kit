import { useCallback, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom';

import {
  ChatAnywhere,
  type ChatAnywhereRef,
  uuid,
  Stream,
  type TMessage,
  Welcome,
  createCard
} from '@agentscope-ai/chat';

import sessionLocalStorage from '../utils/sessionLocalStorage.ts';
import { getSessionId } from '../utils/cookie.ts';
import services from '../services';

import Header from './Header.tsx';

export default function Chat() {
  const refChat = useRef<ChatAnywhereRef>(null);
  // @ts-ignore
  window.ref = refChat;

  const currentQA = useRef<{
    query?: TMessage,
    answer?: TMessage,
    abortController?: AbortController;
  }>({});


  useEffect(() => {
    refChat.current?.updateSession(
      sessionLocalStorage.get()
    );
  }, []);


  const onFinish = useCallback((status: 'finished' | 'interrupted' = 'finished') => {
    if (!currentQA.current.answer) {
      return;
    }
    currentQA.current.answer.msgStatus = status;
    currentQA.current.answer.cards = currentQA.current.answer.cards?.map(item => {
      if (item.code === 'Text') {
        return createCard('Text', {
          ...item.data,
          msgStatus: status,
        });
      }
      return item;
    }) || [];
    if (status === 'interrupted') {
      currentQA.current.answer.cards.push(
        createCard('Interrupted', {})
      );
    }
    refChat.current?.setLoading(false);
    ReactDOM.flushSync(() => {
      // @ts-ignore
      refChat.current?.updateMessage(currentQA.current.answer);
    });
    saveToLocalStorage();
  }, []);

  const saveToLocalStorage = useCallback(async () => {
    // 将当前的消息列表同步到当前 session 中
    ReactDOM.flushSync(() => {
      refChat.current?.updateSessionMessages(refChat.current?.getMessages());
    });
    sessionLocalStorage.set(refChat.current?.getSession());
  }, []);

  const chat = useCallback(async (messages?: TMessage[]) => {
    if (!messages) { return; }

    currentQA.current.answer = {
      id: uuid(),
      content: '',
      cards: [],
      role: 'assistant',
      msgStatus: 'generating',
    }

    refChat.current?.updateMessage(currentQA.current.answer);

    currentQA.current.abortController = new AbortController();

    const { currentSessionKey, sessionList } = sessionLocalStorage.get();

    try {
      const result = await services.chat({
        // @ts-ignore
        chat_sessionId: sessionList.find(session => session.key === currentSessionKey)?.label || '',
        oauth_sessionId: getSessionId(),
        input: JSON.stringify(messages.map(msg => ({
          ...msg,
          content: msg.content || (msg.cards || []).reduce((p, c) => { return p + (c.code === 'Text' ? c.data.content : '') }, '')
        })))
      });

      const contentMap = new Map();
      for await (const chunk of Stream({ readableStream: result }, {})) {
        if (currentQA.current.answer.msgStatus === 'interrupted') {
          currentQA.current.abortController.abort();
          break;
        }

        const data = JSON.parse(chunk.data);
        if (data.model === 'agentrun') {
          if (data.choices) {
            let content = contentMap.get(data.id) || '';
            if (data.choices[0].finish_reason === 'stop') {
              onFinish('finished');
              break;
            }
            content = content + (data.choices[0]?.delta.content || '');
            contentMap.set(data.id, content);
            currentQA.current.answer.cards = Array.from(contentMap).map(([key, value]) => {
              return createCard('Text', {
                content: value,
                typing: true,
                msgStatus: 'generating',
                id: key
              });
            }); 
          }
        } else {
          if (data.object ==='response' && data.status === 'completed') {
            onFinish('finished');
            break;
          } 

          if (data.type === 'text' && data.delta) {
            let content = contentMap.get(data.msg_id) || '';
            content = content + (data.text || '');
            contentMap.set(data.msg_id, content);
            currentQA.current.answer.cards = Array.from(contentMap).map(([key, value]) => {
              return createCard('Text', {
                content: value,
                typing: true,
                msgStatus: 'generating',
                id: key
              });
            }); 
          }
        }
        refChat.current?.updateMessage(currentQA.current.answer);
      }
    } catch (error) {
      console.error(error);
      onFinish('interrupted');
    }
  }, []);

  const onInput = useCallback(async (data: { query: string; }) => {
    const query = {
      id: uuid(),
      cards: [{
        code: 'Text',
        data: {
          content: data.query,
          msgStatus: 'finished'
        }
      }],
      role: 'user',
      msgStatus: 'finished',
    } as TMessage;

    currentQA.current.answer = undefined;
    currentQA.current.query = query;

    refChat.current?.setLoading(true);

    ReactDOM.flushSync(() => {
      refChat.current?.updateMessage(query);
    });

    refChat.current?.scrollToBottom();
    chat(refChat.current?.getMessages());
  }, []);

  const onStop = useCallback(() => {
    onFinish('interrupted');
  }, []);

  const onRegenerate = useCallback((msg: Partial<TMessage>) => {
    ReactDOM.flushSync(() => {
      refChat.current?.removeMessage(msg);
    });
    chat(refChat.current?.getMessages());
  }, []);

  return (
    <div style={{ height: '100vh' }}>
      <ChatAnywhere
        uiConfig={{
          welcome: (
            <Welcome
              style={{ marginTop: 'calc(50vh - 128px)' }}
              title="Nice to meet you!"
              desc="How can I help you today?" />
          ),
          logo: <div style={{ fontFamily: 'Montserrat', fontWeight: 'bold' }}>Agent Identity Demo</div>,
          header: <Header />
        }}
        ref={refChat}
        onInput={{
          onSubmit: onInput,
          zoomable: true,
        }}
        onStop={onStop}
        onRegenerate={onRegenerate}
        onSessionKeyChange={(currentSessionKey) => {
          currentQA.current.answer = undefined;
          currentQA.current.query = undefined;
          sessionLocalStorage.set({ currentSessionKey });
        }} />
    </div>
  )
}