import React, { useCallback, useState, useEffect, useRef } from 'react';
import {
  ReactFlow,
  Background,
  MiniMap,
  useReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import type { Connection, Node, Edge } from '@xyflow/react';
import { FlowControls } from './components/FlowControls';
import { CustomNode } from './components/CustomNode/index';
import { saveFlow, loadFlow } from './utils/flowStorageUtils';

import { initialNodes, initialEdges } from './constants';
import { addNode } from './utils/nodeUtils';
import { addEdge, deleteEdge, updateEdgeStyles } from './utils/edgeUtils';
import { autoLayout } from './utils/layoutUtils';
import { addHistory, onUndo, onRedo, initHistory, getCurrentHistory } from './utils/historyUtils';
import '@xyflow/react/dist/style.css';
import './index.less';

const nodeTypes = {
  customNode: CustomNode,
};

function FlowChart() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(initialEdges);
  const [showMinimap, setShowMinimap] = useState(false);
  const [isStraightLine, setIsStraightLine] = useState(false);

  // 初始化历史记录
  useEffect(() => {
    initHistory(nodes, edges);
  }, []);

  const reactFlowInstance = useReactFlow();

  const handleAddNode = useCallback(() => {
    addNode(nodes, (newNodes) => {
      setNodes(newNodes);
    });
  }, [nodes]);

  const handleConnect = useCallback(
    (params: Connection) => {
      setEdges(addEdge(edges, params.source, params.target));
    },
    [edges]
  );

  const handleAutoLayout = useCallback(() => {
    autoLayout(nodes, edges, setNodes, reactFlowInstance);
  }, [nodes, edges, setNodes, reactFlowInstance]);

  const handleSave = useCallback(() => {
    saveFlow(nodes, edges);
  }, [nodes, edges]);

  const handleLoad = useCallback(() => {
    loadFlow(setNodes, setEdges);
    // 加载后重置历史记录
    setTimeout(() => {
      initHistory(nodes, edges);
    }, 0);
  }, [setNodes, setEdges, nodes, edges]);

  const handleDeleteEdge = useCallback(
    (edgeId: string) => {
      setEdges(deleteEdge(edges, edgeId));
    },
    [edges, setEdges]
  );

  // 自动保存历史记录（带严格防抖）
  const prevNodesRef = useRef<Node[]>([]);
  const prevEdgesRef = useRef<Edge[]>([]);
  useEffect(() => {
    const nodesChanged = JSON.stringify(prevNodesRef.current) !== JSON.stringify(nodes);
    const edgesChanged = JSON.stringify(prevEdgesRef.current) !== JSON.stringify(edges);

    if (nodesChanged || edgesChanged) {
      const currentHistory = getCurrentHistory();
      if (
        (nodes.length > 0 || edges.length > 0) &&
        (!currentHistory ||
          JSON.stringify(currentHistory.nodes) !== JSON.stringify(nodes) ||
          JSON.stringify(currentHistory.edges) !== JSON.stringify(edges))
      ) {
        addHistory(nodes, edges);
      }
      prevNodesRef.current = nodes;
      prevEdgesRef.current = edges;
    }
  }, [nodes, edges]);

  const updatedEdges = updateEdgeStyles(edges, isStraightLine).map((edge) => ({
    ...edge,
    label:
      edge.label &&
      React.cloneElement(edge.label as React.ReactElement, {
        onClick: (e: React.MouseEvent) => {
          (edge.label as React.ReactElement)?.props?.onClick?.(e);
          handleDeleteEdge(edge.id);
        },
      }),
  }));
  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={updatedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        fitView
        nodesDraggable
        edgesFocusable
        panOnScroll
        nodeTypes={nodeTypes}
      >
        <Background />
        {showMinimap && <MiniMap />}
        <FlowControls
          isStraightLine={isStraightLine}
          showMinimap={showMinimap}
          onToggleLine={() => setIsStraightLine(!isStraightLine)}
          onSave={handleSave}
          onLoad={handleLoad}
          onAutoLayout={handleAutoLayout}
          onToggleMinimap={() => setShowMinimap(!showMinimap)}
          onAddNode={handleAddNode}
          onUndo={() => {
            const state = onUndo();
            if (state) {
              // 使用函数式更新确保立即应用状态
              setNodes(() => state.nodes);
              setEdges(() => state.edges);
            }
          }}
          onRedo={() => {
            const state = onRedo();
            if (state) {
              setNodes(state.nodes);
              setEdges(state.edges);
            }
          }}
        />
      </ReactFlow>
    </div>
  );
}

export default function () {
  return (
    <ReactFlowProvider>
      <FlowChart />
    </ReactFlowProvider>
  );
}
