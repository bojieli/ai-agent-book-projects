import { useEffect, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

export const useSessionId = () => {
  const [sessionId, setSessionId] = useState<string>('');

  // 从URL参数中获取session ID
  const getSessionIdFromURL = (): string => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('session_id') || '';
  };

  // 更新URL参数中的session ID
  const updateURLSessionId = (id: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('session_id', id);
    window.history.replaceState({}, '', url.toString());
  };

  // 生成新的session ID并更新URL
  const generateNewSessionId = (): string => {
    const newId = uuidv4();
    setSessionId(newId);
    updateURLSessionId(newId);
    console.log('generateNewSessionId', newId);
    return newId;
  };

  useEffect(() => {
    // 初始化时检查URL中是否有session ID
    const urlSessionId = getSessionIdFromURL();

    if (urlSessionId) {
      // 如果URL中有session ID，使用它
      setSessionId(urlSessionId);
    } else {
      // 如果URL中没有session ID，生成一个新的
      generateNewSessionId();
    }
  }, []);

  return {
    sessionId,
    setSessionId,
    generateNewSessionId,
    updateURLSessionId,
  };
}; 