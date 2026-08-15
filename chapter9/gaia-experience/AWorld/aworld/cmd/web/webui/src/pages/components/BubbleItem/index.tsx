import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import CardDefault from './cardDefault';
import CardLinkList from './cardLinkList';
import './index.less';
import type { ToolCardData } from './utils';
import { extractToolCards } from './utils';

interface BubbleItemProps {
  sessionId: string;
  data: string;
  trace_id: string;
  onOpenWorkspace?: (data: ToolCardData) => void;
  isLoading?: boolean;
}

const BubbleItem: React.FC<BubbleItemProps> = ({ sessionId, data, onOpenWorkspace, isLoading = false }) => {
  // 用于记录上次打开的workspace数据，避免重复调用
  const lastWorkspaceDataRef = useRef<ToolCardData | null>(null);

  // 修改openWorkspace函数，直接调用外部回调
  const openWorkspace = (data: ToolCardData) => {
    if (onOpenWorkspace) {
      onOpenWorkspace(data);
    }
  };

  const { segments } = extractToolCards(data);

  // 比较两个workspace数据是否相同
  const isWorkspaceDataEqual = (data1: ToolCardData | null, data2: ToolCardData | null): boolean => {
    if (!data1 && !data2) return true;
    if (!data1 || !data2) return false;

    // 比较关键字段来判断是否为同一个workspace
    return (
      data1.tool_call_id === data2.tool_call_id &&
      data1.artifacts?.length === data2.artifacts?.length &&
      JSON.stringify(data1.artifacts) === JSON.stringify(data2.artifacts)
    );
  };

  // 自动打开workspace的逻辑 - 只在流式输出过程中自动打开
  useEffect(() => {
    // 只有在流式输出过程中才自动打开workspace
    if (!isLoading) {
      return;
    }

    // 查找最新的具有workspace功能的tool_card（不区分card类型）
    const toolCardSegments = segments.filter(segment => segment.type === 'tool_card');

    // 从最后一个开始查找，找到第一个有artifacts的tool_card
    const latestWorkspaceCard = toolCardSegments
      .slice()
      .reverse()
      .find(segment => {
        return segment.type === 'tool_card' &&
          segment.data?.artifacts?.length > 0;
      });

    if (latestWorkspaceCard && latestWorkspaceCard.type === 'tool_card' && onOpenWorkspace) {
      const currentWorkspaceData = latestWorkspaceCard.data;

      // 检查当前workspace数据是否与上次相同
      if (!isWorkspaceDataEqual(lastWorkspaceDataRef.current, currentWorkspaceData)) {
        // 更新记录的workspace数据
        lastWorkspaceDataRef.current = currentWorkspaceData;

        // 使用requestAnimationFrame确保在下一帧渲染后打开workspace
        const frameId = requestAnimationFrame(() => {
          openWorkspace(currentWorkspaceData);
        });

        return () => cancelAnimationFrame(frameId);
      } else {
        console.log("latest workspace opened!", currentWorkspaceData, lastWorkspaceDataRef.current)
      }
    }
  }, [segments, onOpenWorkspace, openWorkspace, isLoading]);

  // console.log('segments:', segments);
  return (
    <div className="card">
      {segments.map((segment, index) => {
        if (segment.type === 'text') {
          return (
            <div className="markdownbox" key={`text-${index}`}>
              <ReactMarkdown>{segment.content}</ReactMarkdown>
            </div>
          );
        } else if (segment.type === 'tool_card') {
          const cardType = segment.data?.card_type;
          if (cardType === 'tool_call_card_link_list') {
            return <CardLinkList key={`tool-${index}`} sessionId={sessionId} data={segment.data} onOpenWorkspace={openWorkspace} />;
          } else {
            return <CardDefault key={`tool-${index}`} sessionId={sessionId} data={segment.data} onOpenWorkspace={openWorkspace} />;
          }
        }
      })}
      {/* 移除内部的Drawer */}
    </div>
  );
};

export default BubbleItem;
