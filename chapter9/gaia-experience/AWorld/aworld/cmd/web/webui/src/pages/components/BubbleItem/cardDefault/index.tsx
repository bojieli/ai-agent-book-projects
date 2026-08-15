import { MenuUnfoldOutlined } from '@ant-design/icons';
import { Button, Collapse, Space, message } from 'antd';
import React, { useCallback, useState } from 'react';
import type { ToolCardData } from '../utils';
import './index.less';

interface Props {
  sessionId: string;
  data: ToolCardData;
  onOpenWorkspace: (data: ToolCardData) => void;
}

const CardDefault: React.FC<Props> = ({ sessionId, data, onOpenWorkspace }) => {
  // 当前展开的面板keys
  const [activeKeys, setActiveKeys] = useState<string[]>([]);

  // 处理复制
  const handleCopy = useCallback(
    async (panelKey: string) => {
      try {
        const content = panelKey === '1' ? data.arguments : data.results;
        await navigator.clipboard.writeText(content);
        message.success('Copy Successful');
      } catch (error) {
        message.error('Copy Failed');
      }
    },
    [data]
  );
  // 打开workspace
  const handleOpenWorkspace = useCallback(() => {
    if (onOpenWorkspace) {
      onOpenWorkspace(data);
    }
  }, [onOpenWorkspace, sessionId, data]);

  //操作按钮
  const renderExtra = useCallback(
    (panelKey: string) => (
      <Space size="small" onClick={(e) => e.stopPropagation()}>
        <span className="action-btn" onClick={() => handleCopy(panelKey)}>
          Copy
        </span>
      </Space>
    ),
    [handleCopy]
  );

  const items = [
    {
      key: '1',
      label: 'tool_call_arguments',
      extra: renderExtra('1'),
      children: (
        <pre className="pre-wrap">
          <code>{data.arguments}</code>
        </pre>
      )
    },
    {
      key: '2',
      label: 'tool_call_result',
      extra: renderExtra('2'),
      children: (
        <pre className="pre-wrap">
          <code>{data.results}</code>
        </pre>
      )
    }
  ];

  return (
    <div className="defaultbox">
      {data?.artifacts?.length > 0 && (
        <Button type="link" className="btn-workspace" icon={<MenuUnfoldOutlined />} onClick={handleOpenWorkspace}>
          View Workspace
        </Button>
      )}
      <Collapse activeKey={activeKeys} onChange={(keys) => setActiveKeys(Array.isArray(keys) ? keys : [keys])} items={items} />
    </div>
  );
};

export default React.memo(CardDefault);
