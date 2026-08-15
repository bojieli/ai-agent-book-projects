import React, { useState, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  ReactFlowProvider,
  applyNodeChanges
} from '@xyflow/react';
import type { NodeChange } from '@xyflow/react';
import CustomNode from './CustomNode';
import '@xyflow/react/dist/style.css';
import { fetchTraceData } from '@/api/trace';
import { getLayoutedElements } from './layoutUtils';
import './index.less';
import type { TraceXYProps, NodeData, EdgeData } from './TraceXY.types';

const nodeTypes = {
  customNode: CustomNode
};
const TraceXY: React.FC<TraceXYProps> = ({ traceId, drawerVisible }) => {
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((nds) => {
      const updatedNodes = applyNodeChanges(changes, nds);
      return updatedNodes.map((node) => ({
        ...node,
        type: node.type || 'customNode',
        data: (node as NodeData).data
      })) as NodeData[];
    });
  }, []);

  const processNodes = useCallback((rawNodes: any[] = []): NodeData[] => {
    return rawNodes.map((node) => ({
      id: node.span_id || node.id || '',
      type: 'customNode',
      position: node.position || { x: 0, y: 0 },
      data: {
        ...node.data,
        label: node.show_name,
        summary: node.summary || '',
        show_name: node.show_name,
        event_id: node.event_id
      }
    }));
  }, []);

  const processEdges = useCallback((rawEdges: any[] = []): EdgeData[] => {
    return rawEdges.map((edge) => ({
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      className: 'node-edge',
      type: 'smoothstep'
    }));
  }, []);

  const loadAndLayoutElements = useCallback(async () => {
    if (!traceId || !drawerVisible) return;

    setLoading(true);
    setError(null);

    try {
      const result = await fetchTraceData(traceId);
      const nodesWithPosition = processNodes(result?.nodes || []);
      const edgesWithId = processEdges(result?.edges || []);

      const { nodes: layoutedNodes, edges: layoutedEdges } = await getLayoutedElements(
        nodesWithPosition,
        edgesWithId
      );

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    } catch (err) {
      setError('Failed to load trace data, please try again later.');
      console.error('Failed to fetch and build trace elements:', err);
    } finally {
      setLoading(false);
    }
  }, [traceId, drawerVisible, processNodes, processEdges]);

  useEffect(() => {
    loadAndLayoutElements();
  }, [loadAndLayoutElements]);

  return (
    <div className="traceXYbox" style={{ height: '100%', width: '100%' }}>
      {loading && <div className="loading-indicator">Loading...</div>}
      {error && <div className="error-message">{error}</div>}
      {!loading && !error && nodes.length === 0 && (
        <div className="empty-state">No trace data available</div>
      )}
      {nodes.length > 0 && (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          nodesDraggable
          onNodesChange={onNodesChange}
          snapToGrid={true}
          snapGrid={[15, 15]}
          fitView
          minZoom={0.1}
          maxZoom={2}
        >
          <Background gap={16} />
          <Controls />
        </ReactFlow>
      )}
    </div>
  );
};

const TraceXYWithProvider: React.FC<TraceXYProps> = (props) => (
  <ReactFlowProvider>
    <TraceXY {...props} />
  </ReactFlowProvider>
);

export default TraceXYWithProvider;
