import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';

import { clearSessionId } from '../utils/cookie.ts';

import ModelSelect from './ModelSelect.tsx';

export default function Header() {
  const navigator = useNavigate();

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
      <ModelSelect />
      <div style={{ flex: 1 }} />
      <Button
        type="text" 
        onClick={() => {
          clearSessionId();
          navigator('/login', { replace: true });
        }}>
        退出登录
      </Button>
    </div>
  )
}