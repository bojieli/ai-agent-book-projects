import { Position } from '@xyflow/react';

export const initialNodes = [
  {
    id: '1',
    type: 'customNode',
    data: {
      label: 'Start Node',
      nodeType: 'start',
      content: '开始节点，用于设定工作流启动变量',
      input: [
        // { label: 'name', type: 'int' },
        // { label: 'age', type: 'Boolean' }
      ]
    },
    position: { x: 0, y: 0 },
    style: { background: '#E8F8F5', border: '2px solid #1ABC9C', color: '#16A085' },
    sourcePosition: Position.Right,
    targetPosition: Position.Left
  },
  {
    id: '2',
    type: 'customNode',
    data: {
      label: 'End Node',
      nodeType: 'end',
      content: '结束节点，用于返回工作流运行结果',
      output: [
        // { label: 'name', type: 'int' },
        // { label: 'age', type: 'Boolean' }
      ]
    },
    position: { x: 400, y: 0 },
    style: { background: '#FEF9E7', border: '2px solid #F7DC6F', color: '#D4AC0D' },
    sourcePosition: Position.Right,
    targetPosition: Position.Left
  }
];
export const initialEdges = [];
