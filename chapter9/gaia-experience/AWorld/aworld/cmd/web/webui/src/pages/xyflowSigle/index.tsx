import { useCallback, useState } from 'react';
import { ReactFlow, Background, Controls, MiniMap, MarkerType, useNodesState, useEdgesState, addEdge, ControlButton, Position, useReactFlow, ReactFlowProvider } from '@xyflow/react';
import { PlusOutlined, SaveOutlined, FolderOutlined, ReloadOutlined, GlobalOutlined } from '@ant-design/icons';
import type { Node, Edge, Connection } from '@xyflow/react';
import dagre from 'dagre';
import { message } from 'antd';

import '@xyflow/react/dist/style.css';
import './index.less';

// init Nodes
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Strat Node' },
    position: { x: 0, y: 0 },
    style: { background: '#E8F8F5', border: '2px solid #1ABC9C', color: '#16A085' },
    sourcePosition: Position.Right,
    targetPosition: Position.Left
  },
  {
    id: '2',
    type: 'output',
    data: { label: 'End Node' },
    position: { x: 400, y: 0 },
    style: { background: '#FEF9E7', border: '2px solid #F7DC6F', color: '#D4AC0D' },
    sourcePosition: Position.Right,
    targetPosition: Position.Left
  }
];

const initialEdges: Edge[] = [];

function FlowChart() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [showMinimap, setShowMinimap] = useState(false);
  const [isStraightLine, setIsStraightLine] = useState(false);

  const reactFlowInstance = useReactFlow();

  // add nodes
  const addNode = useCallback(() => {
    const randomOffset = () => Math.random() * 50 - 25;

    const startNode = nodes.find((node) => node.type === 'input');
    const endNode = nodes.find((node) => node.type === 'output');
    if (!startNode || !endNode) {
      console.error('Start node or end node not found, unable to add a new node');
      return;
    }

    const newXPosition = endNode.position.x - randomOffset();
    const newYPosition = startNode.position.y + 150 + randomOffset();

    const newNode = {
      id: Date.now().toString(),
      data: { label: `Node ${nodes.length + 1}` },
      position: {
        x: newXPosition,
        y: newYPosition
      },
      style: { background: '#FADDDB', border: '2px solid #E6A5AD', color: '#d58690' },
      sourcePosition: Position.Right,
      targetPosition: Position.Left
    };

    setNodes((prevNodes) => [...prevNodes.filter((node) => node.id !== endNode.id), newNode, endNode]);
  }, [nodes, setNodes]);

  const handleConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            markerEnd: { type: MarkerType.ArrowClosed },
            style: { strokeWidth: 2 }
          },
          eds
        )
      );
    },
    [setEdges]
  );

  // const deleteEdge = useCallback(
  //   (edgeId: string) => {
  //     setEdges((eds) => eds.filter((edge) => edge.id !== edgeId));
  //   },
  //   [setEdges]
  // );

  const autoLayout = useCallback(() => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    const nodeWidth = 150;
    const nodeHeight = 50;

    dagreGraph.setGraph({ rankdir: 'LR', nodesep: 50, ranksep: 100 });

    nodes.forEach((node) => {
      dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
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

    setTimeout(() => {
      reactFlowInstance.fitView();
    }, 0);
  }, [nodes, edges, setNodes, reactFlowInstance]);

  const saveFlow = useCallback(() => {
    const flowData = JSON.stringify({ nodes, edges });
    localStorage.setItem('flow-data', flowData);
    message.success('The flowchart layout has been saved!');
  }, [nodes, edges]);

  const loadFlow = useCallback(() => {
    const flowData = localStorage.getItem('flow-data');
    if (flowData) {
      const { nodes, edges } = JSON.parse(flowData);
      setNodes(nodes);
      setEdges(edges);
      message.success('The flowchart layout has been loaded!');
    } else {
      message.info('No saved flowchart layout!');
    }
  }, [setNodes, setEdges]);

  const updatedEdges = edges.map((edge) => ({
    ...edge,
    type: isStraightLine ? 'straight' : 'default',
    style: {
      ...edge.style,
      strokeWidth: 2,
      ...(isStraightLine ? { stroke: '#b1b1b7', strokeDasharray: '0' } : {})
    }
  }));
  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <ReactFlow nodes={nodes} edges={updatedEdges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={handleConnect} fitView nodesDraggable edgesFocusable panOnScroll>
        <Background />
        {showMinimap && <MiniMap />}
        <Controls style={{ left: '50%', transform: 'translateX(-50%)' }}>
          <ControlButton onClick={() => setIsStraightLine(!isStraightLine)} title={isStraightLine ? 'Switch to curved line' : 'Switch to straight line'}>
            {isStraightLine ? '—' : '~'}
          </ControlButton>
          <ControlButton onClick={saveFlow} title="Save flowchart">
            <SaveOutlined />
          </ControlButton>
          <ControlButton onClick={loadFlow} title="Load flowchart">
            <FolderOutlined />
          </ControlButton>
          <ControlButton onClick={autoLayout} title="Auto Layout">
            <ReloadOutlined />
          </ControlButton>
          <ControlButton onClick={() => setShowMinimap(!showMinimap)} title={showMinimap ? 'Hide minimap' : 'Show minimap'}>
            <GlobalOutlined />
          </ControlButton>

          <ControlButton onClick={addNode} title="Add Node">
            <PlusOutlined />
          </ControlButton>
        </Controls>
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
