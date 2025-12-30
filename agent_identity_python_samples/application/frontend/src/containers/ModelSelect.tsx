import React from 'react';
import { Dropdown, Button } from 'antd';

import { SparkDownLine } from '@agentscope-ai/icons';

const items = [
  {
    key: 'qwen3-max',
    label: <Model name="qwen3-max" />
  }
];

function Model(props: {
  name?: string;
  size?: number;
  arrow?: boolean
}) {
  const { name = '', size = 12, arrow = false } = props;
  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
      <img src="https://img.alicdn.com/imgextra/i4/O1CN01SdyYTH1Kfz6skC36o_!!6000000001192-2-tps-96-96.png" style={{ width: 20, height: 20 }} />
      <div style={{ fontSize: size }}>{name}</div>
      {
        arrow && <SparkDownLine />
      }
    </div>
  )
}

export default function ModelSelect() {
  const current = items[0];

  return (
    <Dropdown
      menu={{
        items,
        selectable: true,
        onSelect: () => {}
      }}>
      <Button type="text" style={{ padding: '0 6px' }}>
        {current?.label ? React.cloneElement(current.label, { size: 16, arrow: true }) : null}
      </Button>
    </Dropdown>
  )
}