import { useState, useEffect } from 'react';
import { Button, Space } from 'antd';

import services from '../../services';

export default function PageLogin() {
  const [stateLoading, setStateLoading] = useState(false);
  const [stateAuthorizeUrl, setStateAuthorizeUrl] = useState('');

  const raiseGetAuthorizeUrl = async () => {
    setStateLoading(true);
    try {
      const url = await services.auth();
      setStateAuthorizeUrl(url);
    } catch {
      setStateAuthorizeUrl('');
    } finally {
      setStateLoading(false);
    }
  };

  useEffect(() => {
    raiseGetAuthorizeUrl();
  }, []);

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center'
    }}>
      <Space direction="vertical" size="middle">
        <h2>OAuth 登录</h2>
        <Button
          type="primary"
          size="large"
          loading={stateLoading}
          onClick={() => {
            window.location.href = stateAuthorizeUrl.toString();
          }}
          style={{ 
            width: 280,
            backgroundColor: '#0064C8',
            color: '#f0f2f5',
            border: '1px solid #d9d9d9'
          }}>
          阿里云登录
        </Button>
      </Space>
    </div>
  );
};
