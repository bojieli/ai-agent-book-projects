import React, { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';
import { fetchTraceData } from '@/api/trace';
import { treeToMermaid } from './mermaidUtils';
import './index.less';

interface TraceProps {
  traceId?: string;
  drawerVisible?: boolean;
}

const Trace: React.FC<TraceProps> = ({ traceId, drawerVisible }) => {
  const diagramRef = useRef<HTMLDivElement>(null);
  const [mermaidCode, setMermaidCode] = useState<string>('');
  const isFetching = useRef(false);

  const renderError = (message: string) => {
    return `graph TD\n  A[${message}]`;
  };

  const handleFetchTrace = useCallback(async () => {
    if (!traceId || isFetching.current) return;
    isFetching.current = true;
    try {
      const result = await fetchTraceData(traceId);
      if (!result?.data) throw new Error('Invalid trace data format');
      
      const mermaidData = treeToMermaid(result.data);
      if (!mermaidData.includes('graph') && !mermaidData.includes('flowchart')) {
        throw new Error(`Invalid mermaid data format`);
      }
      setMermaidCode(mermaidData);
    } catch (error) {
      console.error('Trace processing error:', error);
      setMermaidCode(renderError(error instanceof Error ? error.message : 'Data Processing Error'));
    } finally {
      isFetching.current = false;
    }
  }, [traceId]);

  useEffect(() => {
    if (traceId && drawerVisible) {
      handleFetchTrace();
    }
    return () => {
      // Cleanup if component unmounts during fetch
    };
  }, [traceId, drawerVisible, handleFetchTrace]);

  useEffect(() => {
    if (!mermaidCode) return;

    const renderMermaid = async () => {
      try {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'loose'
        });
        
        if (diagramRef.current) {
          diagramRef.current.innerHTML = mermaidCode;
          await mermaid.run({
            nodes: [diagramRef.current],
            suppressErrors: true
          });
        }
      } catch (error) {
        console.error('Mermaid error:', error);
        setMermaidCode(renderError(error instanceof Error ? error.message : 'Rendering Error'));
      }
    };

    renderMermaid();
  }, [mermaidCode]);

  return (
    <div className="tracebox">
      <div ref={diagramRef} className="mermaid">
        {mermaidCode ||
          `graph TD
          A[loading...]`}
      </div>
      <p className='trace-id'>traceId: {traceId}</p>
    </div>
  );
};

export default Trace;
