import type { Node, Edge } from '@xyflow/react';

// 流程图状态类型
type FlowState = {
  nodes: Node[];
  edges: Edge[];
};

// 操作历史栈
let historyStack: FlowState[] = [];
let currentIndex = -1;
let isUndoRedoInProgress = false;

// 初始化历史记录
export const initHistory = (nodes: Node[], edges: Edge[]) => {
  historyStack = [
    {
      nodes: JSON.parse(JSON.stringify(nodes)),
      edges: JSON.parse(JSON.stringify(edges))
    }
  ];
  currentIndex = 0;
};

/**
 * 添加新操作到历史记录
 */
export const addHistory = (nodes: Node[], edges: Edge[]) => {
  console.log('addHistory添加记录')
  if (isUndoRedoInProgress) {
    isUndoRedoInProgress = false;
    return;
  }
  const newState = {
    nodes: JSON.parse(JSON.stringify(nodes)),
    edges: JSON.parse(JSON.stringify(edges))
  };

  // 更严格的状态变化检测
  const prevState = currentIndex >= 0 ? historyStack[currentIndex] : null;
  if (prevState && prevState.nodes.length === newState.nodes.length && prevState.edges.length === newState.edges.length && JSON.stringify(prevState.nodes) === JSON.stringify(newState.nodes) && JSON.stringify(prevState.edges) === JSON.stringify(newState.edges)) {
    console.log('[History] 状态未变化，跳过保存');
    return;
  }

  // 清除当前索引之后的操作（如果有重做操作未执行）
  const removedCount = historyStack.length - (currentIndex + 1);
  historyStack.splice(currentIndex + 1);
  historyStack.push(newState);
  currentIndex = historyStack.length - 1;

  console.log(`[History] 新增，currentIndex=${currentIndex}, 节点数=${nodes.length}, 边数=${edges.length}, 移除记录=${removedCount}, 调用栈:`);
};

/**
 * 撤销操作
 */
export const onUndo = (): FlowState | null => {
  if (currentIndex <= 0) {
    return null;
  }

  isUndoRedoInProgress = true;
  const prevIndex = currentIndex - 1;
  const prevState = historyStack[prevIndex];

  currentIndex = prevIndex;
  return {
    nodes: [...prevState.nodes],
    edges: [...prevState.edges]
  };
};

/**
 * 重做操作
 */
export const onRedo = (): FlowState | null => {
  if (currentIndex >= historyStack.length - 1) {
    return null;
  }

  isUndoRedoInProgress = true;
  currentIndex++;
  const nextState = historyStack[currentIndex];

  return nextState;
};

/**
 * 获取当前历史状态
 */
export const getCurrentHistory = (): FlowState | null => {
  if (currentIndex < 0) return null;
  return historyStack[currentIndex];
};

/**
 * 清除历史记录
 */
export const clearHistory = () => {
  historyStack.length = 0;
  currentIndex = -1;
};
