import { useEffect, useState } from 'react';

export const useAgentId = () => {
  const [agentId, setAgentId] = useState<string>('');

  // 从URL参数中获取agent ID
  const getAgentIdFromURL = (): string => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('agentid') || '';
  };

  // 更新URL参数中的agent ID
  const updateURLAgentId = (id: string) => {
    const url = new URL(window.location.href);
    if (id) {
      url.searchParams.set('agentid', id);
    } else {
      url.searchParams.delete('agentid');
    }
    window.history.replaceState({}, '', url.toString());
  };

  // 设置新的agent ID并更新URL
  const setAgentIdAndUpdateURL = (id: string) => {
    setAgentId(id);
    updateURLAgentId(id);
  };

  useEffect(() => {
    // 初始化时检查URL中是否有agent ID
    const urlAgentId = getAgentIdFromURL();
    
    if (urlAgentId) {
      // 如果URL中有agent ID，使用它
      setAgentId(urlAgentId);
    }
  }, []);

  return {
    agentId,
    setAgentIdAndUpdateURL,
    updateURLAgentId,
  };
}; 