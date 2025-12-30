import { ConfigProvider, carbonTheme } from '@agentscope-ai/design';

import Chat from '../../containers/Chat';
export default function PageChat() {
    
  return (
    <ConfigProvider {...carbonTheme} prefix="agentidentity-demo-chat" prefixCls="agentidentity-demo-chat">
      <Chat />
    </ConfigProvider>
);
}