import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

import services from '../../services';
import { setSessionId } from '../../utils/cookie.ts';

export default function PageAuth() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const code = searchParams.get('code') || '';
  const state = searchParams.get('state') || '';

  const callbackOAuth = async (code: string) => {
    try {
      const { sessionId } = await services.callbackOAuth({ authorizeCode: code, state });
      setSessionId(sessionId);
      navigate('/', { replace: true }); // 跳回首页（此时有 sessionId）
    } catch (error) {
      console.error(error);
      navigate('/login', { replace: true });
    }
  };

  useEffect(() => {
    if (code) {
      callbackOAuth(code);
    } else {
      navigate('/login', { replace: true });
    }
  }, [code, navigate]);

  return <div>正在登录...</div>;
}