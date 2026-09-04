import { RouterProvider, createBrowserRouter, Navigate } from 'react-router-dom';

import PageChat from './pages/chat';
import PageLogin from './pages/login';
import PageAuth from './pages/authorize';
import { getSessionId } from './utils/cookie.ts';

function AuthGuard() {
  const sessionId = getSessionId();
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');

  // 同步决策（关键！）
  if (sessionId) {
    return <PageChat />;
  }

  if (code) {
    return <Navigate to={`/authorize?code=${code}&state=${state}`} replace />;
  }

  // 未认证 → 跳转登录
  return <Navigate to="/login" replace />;
}

// 路由定义
const router = createBrowserRouter([
  { path: '/login', element: <PageLogin />},
  { path: '/authorize', element: <PageAuth />},
  { path: '*', element: <AuthGuard />}
]);

function App() {
  return (
    <div style={{ height: '100vh' }}>
      <RouterProvider router={router} />
    </div>
  );
}

export default App;