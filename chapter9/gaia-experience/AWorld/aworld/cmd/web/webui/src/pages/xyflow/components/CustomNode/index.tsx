import React, { useState } from 'react';
import { Handle, Position, useNodes, useReactFlow } from '@xyflow/react';
import type { Node, NodeProps } from '@xyflow/react';
import { deleteNode } from '@/pages/xyflow/utils/nodeUtils';
import { Tag, Drawer, Dropdown } from 'antd';
import { EllipsisOutlined, DeleteOutlined, CopyOutlined } from '@ant-design/icons';
import { NodeEditor } from '../NodeEditor';

interface NodeIOItem {
  id: string;
  label: string;
  type: 'string' | 'number' | 'boolean';
  defaultValue?: string;
}

interface CustomNodeData
  extends Node<{
    id: string;
    label: string;
    content?: React.ReactNode;
    input?: NodeIOItem[];
    output?: NodeIOItem[];
    nodeType?: 'start' | 'end' | 'default';
  }> {}

interface CustomNodeProps extends NodeProps<CustomNodeData> {}

export const CustomNode: React.FC<CustomNodeProps> = ({ id, data }) => {
  const { label, content, input, output } = data;
  const nodes = useNodes();
  const reactFlowInstance = useReactFlow();
  const { setNodes } = reactFlowInstance;

  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [pendingData, setPendingData] = useState<Partial<CustomNodeData['data']>>({});
  const [editingData, setEditingData] = useState({
    content: typeof content === 'string' ? content : '',
    input: input || []
  });

  React.useEffect(() => {
    setEditingData({
      content: typeof content === 'string' ? content : '',
      input: input || []
    });
  }, [content, input]);

  const handleNodeClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDrawerOpen(true);
  };
  const handleDrawerClose = (e: React.MouseEvent | React.KeyboardEvent) => {
    if ('stopPropagation' in e) {
      e.stopPropagation();
    }
    if (Object.keys(pendingData).length > 0) {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === id) {
            return {
              ...node,
              data: {
                ...node.data,
                ...pendingData
              }
            };
          }
          return node;
        })
      );
    }
    setIsDrawerOpen(false);
  };
  const renderIO = (title: string, items?: NodeIOItem[]) => {
    return (
      <div className="custom-node-io">
        <span>{title}：</span>
        {items?.map((item) => (
          <Tag key={item.label}>
            {item.type}.<strong>{item.label}</strong>
          </Tag>
        ))}
      </div>
    );
  };

  return (
    <div className="custom-node" onClick={handleNodeClick}>
      <div className="custom-node-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <span>{label}</span>
          {data.nodeType !== 'start' && data.nodeType !== 'end' && (
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'delete',
                    label: '删除',
                    icon: <DeleteOutlined />,
                    onClick: (e) => {
                      e.domEvent.stopPropagation();
                      deleteNode(nodes, setNodes, id);
                    }
                  },
                  {
                    key: 'duplicate',
                    label: '创建副本',
                    icon: <CopyOutlined />,
                    onClick: (e) => {
                      e.domEvent.stopPropagation();
                      alert('暂不支持');
                    }
                  }
                ]
              }}
              trigger={['click']}
            >
              <EllipsisOutlined
                style={{ cursor: 'pointer' }}
                onClick={(e) => e.stopPropagation()}
              />
            </Dropdown>
          )}
        </div>
      </div>
      <div className="custom-node-body">
        <div className="custom-node-content">
          <div>{editingData.content || 'Custom Node Content'}</div>
          {data.nodeType !== 'end' && renderIO('输入', input)}
          {data.nodeType !== 'start' && renderIO('输出', output)}
        </div>
      </div>
      {data.nodeType !== 'start' && <Handle type="target" position={Position.Left} />}
      {data.nodeType !== 'end' && <Handle type="source" position={Position.Right} />}
      <Drawer
        title={label}
        placement="right"
        closable={true}
        maskClosable={true}
        onClose={handleDrawerClose}
        open={isDrawerOpen}
        width={500}
        keyboard={true}
      >
        <NodeEditor
          node={{
            id,
            position: { x: 0, y: 0 },
            data: { ...data, ...editingData }
          }}
          onUpdate={(updatedNode) => {
            setPendingData((prev) => ({
              ...prev,
              ...updatedNode.data
            }));
          }}
          onClose={() => handleDrawerClose({ stopPropagation: () => {} } as React.MouseEvent)}
        />
      </Drawer>
    </div>
  );
};
