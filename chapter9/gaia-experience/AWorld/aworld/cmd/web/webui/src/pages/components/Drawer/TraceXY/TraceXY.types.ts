import type { Node, Edge } from '@xyflow/react';

export interface CustomNodeData {
  show_name?: string;
  event_id?: string;
  summary?: string | { summary: string };
  [key: string]: any;
}

export interface NodeData extends Node {
  data: CustomNodeData;
  type: string;
}

export interface EdgeData extends Edge {
  [key: string]: any;
}

export interface TraceXYProps {
  traceId?: string;
  traceQuery?: string;
  drawerVisible?: boolean;
}
