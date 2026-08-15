import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { ThoughtChain } from '@ant-design/x';
import type { ThoughtChainProps, ThoughtChainItem } from '@ant-design/x';
import { Card, Typography, message } from 'antd';
import { fetchTraceData } from '@/api/trace';

const { Paragraph } = Typography;

interface TraceProps {
  traceId?: string;
  drawerVisible?: boolean;
}

type TraceNodeStatus = 'success' | 'pending' | 'error';

interface TraceNode {
  id: string;
  status?: TraceNodeStatus;
  show_name: string;
  children?: TraceNode[];
  description?: string;
  event_id: string;
  summary?: string;
  token_usage?: number;
  input_tokens?: number;
  output_tokens?: number;
  use_tools?: string[];
}

const Trace: React.FC<TraceProps> = ({ traceId, drawerVisible }) => {
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [traceData, setTraceData] = useState<TraceNode[]>([]);

  const fetchData = useCallback(async () => {
    if (!traceId || !drawerVisible) return;
    try {
      const res = await fetchTraceData(traceId);

      const validateStatus = (status?: string): TraceNodeStatus | undefined => {
        return status === 'success' || status === 'pending' || status === 'error' ? (status as TraceNodeStatus) : undefined;
      };

      const validatedData = (res.data || []).map((item: TraceNode) => ({
        ...item,
        status: validateStatus(item.status)
      }));
      setTraceData(validatedData);
      // Expand the first node by default
      if (validatedData?.[0]?.event_id) {
        setExpandedKeys([validatedData[0].event_id]);
      }
    } catch (err) {
      message.error('Failed to fetch trace data');
      console.error(err);
    }
  }, [traceId, drawerVisible]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const renderNodeContent = useCallback(
    (node: TraceNode) => (
      <>
        {node.token_usage && <p>token_usage: {node.token_usage}</p>}
        {node.input_tokens && <p>input_tokens: {node.input_tokens}</p>}
        {node.output_tokens && <p>output_tokens: {node.output_tokens}</p>}
        {node.use_tools?.length && <p>use_tools: {node.use_tools.join(', ')}</p>}
        {node.summary && (
          <Typography>
            <Paragraph>
              <pre>{JSON.stringify(JSON.parse(node.summary), null, 2)}</pre>
            </Paragraph>
          </Typography>
        )}
        {node.children?.length ? <ThoughtChain items={convertToItems(node.children)} /> : null}
      </>
    ),
    []
  );

  const convertToItems = useCallback(
    (nodes: TraceNode[]): ThoughtChainItem[] => {
      return nodes.map((node) => ({
        key: node.event_id,
        title: node.show_name,
        description: node.event_id,
        content: renderNodeContent(node),
        status: node.status || 'pending'
      }));
    },
    [renderNodeContent]
  );

  const items = useMemo(() => convertToItems(traceData), [traceData, convertToItems]);

  const collapsible: ThoughtChainProps['collapsible'] = useMemo(() => {
    return {
      expandedKeys,
      onExpand: (keys: string[]) => setExpandedKeys(keys)
    };
  }, [expandedKeys]);

  return (
    <Card style={{ width: 650 }}>
      <ThoughtChain items={items} collapsible={collapsible} />
    </Card>
  );
};

export default Trace;
