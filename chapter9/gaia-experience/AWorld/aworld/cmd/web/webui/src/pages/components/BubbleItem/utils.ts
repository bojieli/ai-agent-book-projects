export interface ToolCardData {
  tool_type: string;
  tool_name: string;
  function_name: string;
  tool_call_id: string;
  arguments: string;
  results: string;
  card_type: string;
  card_data: any;
  artifacts: any[];
}

type ContentSegment =
  | { type: 'text'; content: string }
  | { type: 'tool_card'; data: ToolCardData; raw: string };

export interface ParsedContent {
  segments: ContentSegment[];
}

export const extractToolCards = (content: string): ParsedContent => {
  const toolCardRegex = /(.*?)(```tool_card\s*({[\s\S]*?})\s*```)/gs;
  const segments: ContentSegment[] = [];
  let lastIndex = 0;

  let match;
  while ((match = toolCardRegex.exec(content)) !== null) {
    const [, textBefore, fullToolCard, toolCardJson] = match;

    // 添加文本内容
    if (textBefore) {
      segments.push({
        type: 'text',
        content: textBefore.trim()
      });
    }

    // 添加工具卡片
    try {
      segments.push({
        type: 'tool_card',
        data: JSON.parse(toolCardJson),
        raw: fullToolCard.trim()
      });
    } catch (e) {
      console.error('Failed to parse tool_card JSON:', e);
      // 如果解析失败，仍保留原始文本
      segments.push({
        type: 'text',
        content: fullToolCard.trim()
      });
    }

    lastIndex = toolCardRegex.lastIndex;
  }

  // 添加最后剩余的文本内容
  const remainingText = content.slice(lastIndex);
  if (remainingText.trim()) {
    segments.push({
      type: 'text',
      content: remainingText.trim()
    });
  }

  return { segments };
};
