import type { Edge } from '@xyflow/react';
import { MarkerType } from '@xyflow/react';
/**
 * Edge operation functions
 * adding、deleting
 */
export const addEdge = (edges: Edge[], source: string, target: string): Edge[] => {
  const newEdge = {
    id: `${source}-${target}-${Date.now()}`,
    source,
    target
  };

  return [...edges, newEdge];
};

export const deleteEdge = (edges: Edge[], edgeId: string): Edge[] => {
  return edges.filter((edge) => edge.id !== edgeId);
};

export const updateEdgeStyles = (edges: Edge[], isStraightLine: boolean): Edge[] => {
  return edges.map((edge) => ({
    ...edge,
    type: isStraightLine ? 'straight' : 'default',
    markerEnd: { type: MarkerType.ArrowClosed },
    style: {
      ...edge.style,
      strokeWidth: 2,
      ...(isStraightLine ? { stroke: '#b1b1b7', strokeDasharray: '0' } : {})
    }
  }));
};
