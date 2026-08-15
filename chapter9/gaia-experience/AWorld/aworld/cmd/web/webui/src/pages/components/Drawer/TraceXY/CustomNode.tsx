import React from 'react';
import { Tooltip, Typography } from 'antd';
import { Position, Handle } from '@xyflow/react';
import type { CustomNodeData } from './TraceXY.types';

interface CustomNodeProps {
  data: {
    data: CustomNodeData;
  };
  isFirst?: boolean;
  isLast?: boolean;
}

const CustomNode: React.FC<CustomNodeProps> = ({ data, isFirst, isLast }) => {
  const nodeData: CustomNodeData = data || {};
  const summary = nodeData.summary
    ? (typeof nodeData.summary === 'string'
        ? JSON.parse(nodeData.summary).summary
        : nodeData.summary?.summary) || ''
    : '';
  const tooltipContent = nodeData.event_id ? (
    <div className="Tooltipbox">
      {summary.length > 100 ? summary : ''}
      <div>{nodeData.event_id}</div>
    </div>
  ) : null;
  return (
    <Tooltip title={tooltipContent} placement="bottom" className="Tooltipbox">
      <div className="custom-node">
        <Typography.Paragraph className="summary" ellipsis={{ rows: 4 }}>
          {summary}
        </Typography.Paragraph>
        <div className="name">{nodeData.show_name || 'Unnamed Node'}</div>
        {!isFirst && (
          <Handle
            type="target"
            position={Position.Top}
          />
        )}
        {!isLast && (
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom"
          />
        )}
         {nodeData.sourceHandle?.includes('right') && (
           <Handle type="source" position={Position.Right} id="right" />
         )}
         {nodeData.sourceHandle?.includes('left') && (
           <Handle type="source" position={Position.Left} id="left" />
         )}
      </div>
    </Tooltip>
  );
};
export default CustomNode;
