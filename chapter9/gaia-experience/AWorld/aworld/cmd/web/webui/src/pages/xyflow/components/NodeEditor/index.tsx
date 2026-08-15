import React, { useCallback, useMemo } from 'react';
import { Button, Input, Table, Select, Collapse } from 'antd';
import type { ColumnType } from 'antd/es/table';
import './index.less';
import { PlusOutlined } from '@ant-design/icons';
import type { Node } from '@xyflow/react';

const { Option } = Select;

interface NodeIOItem {
  id: string;
  label: string;
  type: 'string' | 'number' | 'boolean';
  defaultValue?: string;
}

interface NodeEditorProps {
  node: Node<{
    id: string;
    label: string;
    content?: React.ReactNode;
    input?: NodeIOItem[];
    output?: NodeIOItem[];
  }>;
  onUpdate: (node: Node) => void;
  onClose: () => void;
}

export const NodeEditor: React.FC<NodeEditorProps> = ({ node, onUpdate }) => {
  const [editingContent, setEditingContent] = React.useState(
    typeof node.data.content === 'string' ? node.data.content : ''
  );
  const [editingInputs, setEditingInputs] = React.useState<NodeIOItem[]>(node.data.input || []);

  React.useEffect(() => {
    setEditingContent(typeof node.data.content === 'string' ? node.data.content : '');
    setEditingInputs(node.data.input || []);
  }, [node.data.content, node.data.input]);

  const handleUpdate = useCallback(
    (newData: Partial<typeof node.data>) => {
      onUpdate({
        ...node,
        data: {
          ...node.data,
          ...newData
        }
      });
    },
    [node, onUpdate]
  );

  const handleInputChange = useCallback(
    <K extends keyof NodeIOItem>(index: number, field: K, value: NodeIOItem[K]) => {
      const newInputs = [...editingInputs];
      newInputs[index][field] = value;
      setEditingInputs(newInputs);
      handleUpdate({ input: newInputs });
    },
    [editingInputs, handleUpdate]
  );

  return (
    <>
      <div>{editingContent}</div>

      <Collapse defaultActiveKey={['input']} bordered={false} className="node-editor-collapse">
        <Collapse.Panel
          header="输入"
          key="input"
          extra={
            <Button
              className="node-editor-collapse-btn"
              icon={<PlusOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                const newInputs: NodeIOItem[] = [
                  ...editingInputs,
                  {
                    id: `input-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                    label: '',
                    type: 'string' as const,
                    defaultValue: ''
                  }
                ];
                setEditingInputs(newInputs);
                handleUpdate({ input: newInputs });
              }}
            />
          }
        >
          <Table
            dataSource={editingInputs}
            rowKey={(record) => record.id}
            pagination={false}
            columns={useMemo<Array<ColumnType<NodeIOItem>>>(
              () => [
                {
                  title: '变量名',
                  dataIndex: 'label',
                  render: (text: string, _: NodeIOItem, index: number) => (
                    <Input
                      key={index}
                      value={text as 'string' | 'number' | 'boolean'}
                      onChange={(e) => handleInputChange(index, 'label', e.target.value)}
                      placeholder="Variable name"
                    />
                  )
                },
                {
                  title: '变量值',
                  dataIndex: 'type',
                  render: (text: string, _: NodeIOItem, index: number) => (
                    <Select
                      value={text as 'string' | 'number' | 'boolean'}
                      style={{ width: '100%' }}
                      onChange={(value: 'string' | 'number' | 'boolean') =>
                        handleInputChange(index, 'type', value)
                      }
                    >
                      <Option value="string">String</Option>
                      <Option value="number">Number</Option>
                      <Option value="boolean">Boolean</Option>
                    </Select>
                  )
                },
                {
                  title: '',
                  dataIndex: 'defaultValue',
                  render: (text: string | undefined, _record: NodeIOItem, index: number) => (
                    <Input
                      value={text}
                      onChange={(e) => handleInputChange(index, 'defaultValue', e.target.value)}
                      placeholder="Default value"
                    />
                  )
                },
                {
                  title: '',
                  render: (_text, _record: NodeIOItem, index: number) => (
                    <Button
                      danger
                      onClick={() => {
                        const newInputs = editingInputs.filter((_, i) => i !== index);
                        setEditingInputs(newInputs);
                        handleUpdate({ input: newInputs });
                      }}
                    >
                      Delete
                    </Button>
                  )
                }
              ],
              [handleInputChange, editingInputs, handleUpdate]
            )}
          />
        </Collapse.Panel>
      </Collapse>
      <Collapse defaultActiveKey={['output']} bordered={false} className="node-editor-collapse">
        <Collapse.Panel header="输出" key="output">
          <Input.TextArea
            value={editingContent || ''}
            onChange={(e) => {
              const newValue = e.target.value;
              setEditingContent(newValue);
              handleUpdate({ content: newValue });
            }}
            placeholder="Enter node content"
            autoSize={{ minRows: 3, maxRows: 10 }}
          />
        </Collapse.Panel>
      </Collapse>
    </>
  );
};
