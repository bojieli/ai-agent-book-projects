import dagre from 'dagre';

const calculateEdgeLength = (
  sourcePos: { x: number; y: number },
  targetPos: { x: number; y: number }
): number => Math.hypot(targetPos.x - sourcePos.x, targetPos.y - sourcePos.y);

export const getLayoutedElements = (nodes: any[], edges: any[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: 'TB',
    nodesep: 50,
    ranksep: 50
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  edges.forEach((edge) => {
    const sourceNode = nodes.find((n) => n.id === edge.source);
    const targetNode = nodes.find((n) => n.id === edge.target);
    if (!sourceNode || !targetNode) return;

    const sourcePos = dagreGraph.node(edge.source);
    const targetPos = dagreGraph.node(edge.target);
    const length = calculateEdgeLength(sourcePos, targetPos);

    if (length > 300) {
      const direction = targetPos.x > sourcePos.x ? 'right' : 'left';

      sourceNode.data = sourceNode.data || {};
      sourceNode.data.sourceHandle = sourceNode.data.sourceHandle || [];

      sourceNode.data.sourceHandle.push(direction);
      edge.sourceHandle = direction;
    }
  });

  const updatedNodes = nodes.map((node) => {
    const position = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: position.x - 100,
        y: position.y - 50
      }
    };
  });

  return {
    nodes: updatedNodes,
    edges: edges
  };
};
