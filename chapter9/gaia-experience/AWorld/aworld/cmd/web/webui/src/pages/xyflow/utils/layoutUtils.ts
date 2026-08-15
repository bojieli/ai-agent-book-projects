/**
 * Auto layout
 * use dagre library
 */
import type { Node, Edge } from '@xyflow/react';
import type { useReactFlow } from '@xyflow/react';
import dagre from 'dagre';

export const autoLayout = (
  nodes: Node[],
  edges: Edge[],
  setNodes: (nodes: Node[]) => void,
  reactFlowInstance: ReturnType<typeof useReactFlow>
): void => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  const nodeWidth = 200;
  const nodeHeight = 100;

  dagreGraph.setGraph({
    rankdir: 'LR',
    nodesep: 50,
    ranksep: 100
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: nodeWidth,
      height: nodeHeight
    });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const updatedNodes = nodes.map((node) => {
    const layoutNode = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: layoutNode.x,
        y: layoutNode.y
      }
    };
  });
  setNodes(updatedNodes);
  console.log('auto：', updatedNodes);
  console.log('edges:', edges);
  setTimeout(() => {
    reactFlowInstance.fitView();
  }, 0);
};
