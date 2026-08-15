import type { Node, Edge } from '@xyflow/react';
import { message } from 'antd';

export const saveFlow = (nodes: Node[], edges: Edge[]) => {
  const flowData = JSON.stringify({ nodes, edges });
  localStorage.setItem('flow-data', flowData);
  message.success('The flowchart layout has been saved!');
};

export const loadFlow = (setNodes: (nodes: Node[]) => void, setEdges: (edges: Edge[]) => void) => {
  const flowData = localStorage.getItem('flow-data');
  if (flowData) {
    const { nodes, edges } = JSON.parse(flowData);
    setNodes(nodes);
    setEdges(edges);
    message.success('The flowchart layout has been loaded!');
  } else {
    message.info('No saved flowchart layout!');
  }
};
