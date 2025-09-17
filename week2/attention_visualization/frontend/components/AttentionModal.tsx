import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';

interface AttentionModalProps {
  isOpen: boolean;
  onClose: () => void;
  tokens: string[];
  attentionWeights: number[][];
}

export default function AttentionModal({ isOpen, onClose, tokens, attentionWeights }: AttentionModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredCell, setHoveredCell] = useState<{ row: number; col: number; value: number } | null>(null);
  const [isRendering, setIsRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [transformMethod, setTransformMethod] = useState<'none' | 'log' | 'log10' | 'sqrt' | 'power' | 'power-extreme' | 'exclude-sink'>('log10');

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setZoomLevel(prev => Math.min(prev * 1.2, 10));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel(prev => Math.max(prev / 1.2, 0.2));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoomLevel(1);
  }, []);

  // Transform attention values for better visualization
  const transformAttention = useCallback((value: number, maxWeight: number, isFirstToken: boolean = false) => {
    switch (transformMethod) {
      case 'none':
        return value / maxWeight;
      
      case 'log':
        // Log transformation to spread out small values
        // Adding 1 to avoid log(0), then normalizing
        const logValue = Math.log(1 + value * 100); // Scale up before log
        const logMax = Math.log(1 + maxWeight * 100);
        return logValue / logMax;
      
      case 'sqrt':
        // Square root transformation - less aggressive than log
        return Math.sqrt(value / maxWeight);
      
      case 'power':
        // Power transformation with exponent < 1 to enhance small values
        return Math.pow(value / maxWeight, 0.3); // Cube root-like transformation
      
      case 'power-extreme':
        // Extreme power transformation for very small values
        // Uses power 0.1 to dramatically enhance tiny attention values
        return Math.pow(value / maxWeight, 0.1);
      
      case 'log10':
        // Base-10 logarithm for a different scale perspective
        // Useful for values spanning multiple orders of magnitude
        const log10Value = Math.log10(1 + value * 1000); // Scale up more before log10
        const log10Max = Math.log10(1 + maxWeight * 1000);
        return log10Value / log10Max;
      
      case 'exclude-sink':
        // Exclude first token (attention sink) from normalization
        // This helps visualize the differences between other tokens
        if (isFirstToken) {
          // Cap the first token at a reasonable visualization value
          return Math.min(value / maxWeight, 0.5);
        }
        // For other tokens, normalize without considering the attention sink
        // This will be handled in the main rendering loop
        return value / maxWeight;
      
      default:
        return value / maxWeight;
    }
  }, [transformMethod]);

  // Handle mouse wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setZoomLevel(prev => Math.min(Math.max(prev * delta, 0.2), 10));
    }
  }, []);

  useEffect(() => {
    if (!isOpen || !canvasRef.current || !tokens?.length || !attentionWeights?.length) return;

    setIsRendering(true);
    setRenderError(null);

    // Use requestAnimationFrame for smooth rendering
    requestAnimationFrame(() => {
      try {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          setRenderError('Failed to get canvas context');
          return;
        }

        // Dynamic cell size based on zoom
        const baseCellSize = 5;
        const cellSize = baseCellSize * zoomLevel;
        const margin = { top: 100, right: 50, bottom: 60, left: 100 };
        
        const numTokens = tokens.length;
        const numRows = Math.min(tokens.length, attentionWeights.length);
        
        const width = numTokens * cellSize + margin.left + margin.right;
        const height = numRows * cellSize + margin.top + margin.bottom;

        // Set canvas size
        canvas.width = width;
        canvas.height = height;

        // Clear canvas
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, width, height);

        // Calculate max weight for color scale (efficient method for large arrays)
        let maxWeight = 0;
        let maxWeightExcludingSink = 0; // For exclude-sink transformation
        
        for (let i = 0; i < attentionWeights.length; i++) {
          for (let j = 0; j < attentionWeights[i].length; j++) {
            const value = attentionWeights[i][j];
            if (value > maxWeight) {
              maxWeight = value;
            }
            // Track max excluding first token (attention sink)
            if (j > 0 && value > maxWeightExcludingSink) {
              maxWeightExcludingSink = value;
            }
          }
        }
        maxWeight = maxWeight || 1; // Prevent division by zero
        maxWeightExcludingSink = maxWeightExcludingSink || 0.001; // Prevent division by zero

        // Draw cells in chunks to avoid blocking
        const chunkSize = Math.max(50, Math.floor(100 / zoomLevel)); // Adjust chunk size based on zoom
        let currentRow = 0;

        const drawChunk = () => {
          const endRow = Math.min(currentRow + chunkSize, numRows);
          
          for (let i = currentRow; i < endRow; i++) {
            for (let j = 0; j < numTokens; j++) {
              if (i < attentionWeights.length && j < attentionWeights[i].length) {
                const value = attentionWeights[i][j];
                
                // Apply transformation based on selected method
                let intensity;
                if (transformMethod === 'exclude-sink' && j !== 0) {
                  // For exclude-sink, normalize non-first tokens against maxWeightExcludingSink
                  intensity = transformAttention(value, maxWeightExcludingSink, false);
                } else {
                  intensity = transformAttention(value, maxWeight, j === 0);
                }
                
                // Use D3 Viridis color scale (same as preview)
                const color = d3.interpolateViridis(intensity);
                ctx.fillStyle = color;
                
                ctx.fillRect(
                  margin.left + j * cellSize,
                  margin.top + i * cellSize,
                  cellSize - 0.5,
                  cellSize - 0.5
                );
              }
            }
          }
          
          currentRow = endRow;
          
          // Continue with next chunk if not done
          if (currentRow < numRows) {
            requestAnimationFrame(drawChunk);
          } else {
            // Drawing complete, add labels and legend
            drawLabelsAndLegend();
          }
        };

        const drawLabelsAndLegend = () => {
          // Draw labels only if there's enough space
          if (cellSize >= 8) {
            ctx.fillStyle = '#333';
            ctx.font = `${Math.min(10, cellSize * 0.8)}px sans-serif`;
            
            // Sample labels for large matrices
            const labelStep = Math.max(1, Math.ceil(numTokens / (100 / zoomLevel)));
            
            for (let i = 0; i < numTokens; i += labelStep) {
              ctx.save();
              ctx.translate(margin.left + i * cellSize + cellSize / 2, margin.top - 5);
              ctx.rotate(-Math.PI / 4);
              const label = tokens[i].length > 15 ? tokens[i].substring(0, 15) + '...' : tokens[i];
              ctx.fillText(label, 0, 0);
              ctx.restore();

              // Draw row labels
              if (i < numRows) {
                ctx.save();
                ctx.textAlign = 'right';
                const rowLabel = tokens[i].length > 15 ? tokens[i].substring(0, 15) + '...' : tokens[i];
                ctx.fillText(rowLabel, margin.left - 5, margin.top + i * cellSize + cellSize / 2);
                ctx.restore();
              }
            }
          }

          // Draw axis labels
          ctx.fillStyle = '#333';
          ctx.font = 'bold 14px sans-serif';
          ctx.textAlign = 'center';
          
          // Top label
          ctx.fillText('To Tokens (Attended)', width / 2, 20);
          
          // Left label (rotated)
          ctx.save();
          ctx.translate(20, height / 2);
          ctx.rotate(-Math.PI / 2);
          ctx.fillText('From Tokens (Attending)', 0, 0);
          ctx.restore();

          // Draw color scale legend
          const legendWidth = 200;
          const legendHeight = 15;
          const legendX = (width - legendWidth) / 2;
          const legendY = height - 40;

          // Draw gradient with D3 Viridis colors (same as cells)
          for (let i = 0; i <= legendWidth; i++) {
            const intensity = i / legendWidth;
            const color = d3.interpolateViridis(intensity);
            ctx.fillStyle = color;
            ctx.fillRect(legendX + i, legendY, 1, legendHeight);
          }

          // Legend labels
          ctx.fillStyle = '#333';
          ctx.font = '10px sans-serif';
          ctx.textAlign = 'left';
          ctx.fillText('0', legendX, legendY + legendHeight + 12);
          ctx.textAlign = 'center';
          ctx.fillText('Attention Weight', legendX + legendWidth / 2, legendY - 5);
          ctx.textAlign = 'right';
          ctx.fillText(maxWeight.toFixed(2), legendX + legendWidth, legendY + legendHeight + 12);

          setIsRendering(false);
        };

        // Start drawing chunks
        drawChunk();
      } catch (error: any) {
        console.error('Error rendering attention matrix:', error);
        setRenderError(error.message || 'Failed to render attention matrix');
        setIsRendering(false);
      }
    });

  }, [isOpen, tokens, attentionWeights, zoomLevel, transformMethod, transformAttention]);

  // Handle mouse move for hover info
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !tokens.length || !attentionWeights.length) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const container = containerRef.current;
    
    // Account for scroll position
    const scrollLeft = container?.scrollLeft || 0;
    const scrollTop = container?.scrollTop || 0;
    
    const x = e.clientX - rect.left + scrollLeft;
    const y = e.clientY - rect.top + scrollTop;

    const cellSize = 5 * zoomLevel;
    const margin = { top: 100, left: 100 };

    const col = Math.floor((x - margin.left) / cellSize);
    const row = Math.floor((y - margin.top) / cellSize);

    if (row >= 0 && row < attentionWeights.length && 
        col >= 0 && col < tokens.length && 
        attentionWeights[row] && attentionWeights[row][col] !== undefined) {
      setHoveredCell({
        row,
        col,
        value: attentionWeights[row][col]
      });
    } else {
      setHoveredCell(null);
    }
  };

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        className="relative bg-white rounded-lg shadow-2xl overflow-hidden flex flex-col"
        style={{
          width: '95vw',
          height: '95vh',
          maxWidth: '1800px',
          maxHeight: '95vh'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b bg-white z-10 shrink-0">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Attention Pattern Visualization</h2>
            <p className="text-sm text-gray-600 mt-1">
              Matrix Size: {tokens.length} × {Math.min(tokens.length, attentionWeights.length)} tokens
              {isRendering && <span className="ml-2 text-blue-600">(Rendering...)</span>}
            </p>
          </div>
          
          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
              <button
                onClick={handleZoomOut}
                className="px-2 py-1 bg-white rounded hover:bg-gray-50 transition-colors text-sm"
                title="Zoom Out"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
                </svg>
              </button>
              <span className="px-2 py-1 text-sm font-medium min-w-[60px] text-center">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="px-2 py-1 bg-white rounded hover:bg-gray-50 transition-colors text-sm"
                title="Zoom In"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
                </svg>
              </button>
              <button
                onClick={handleZoomReset}
                className="px-2 py-1 bg-white rounded hover:bg-gray-50 transition-colors text-sm"
                title="Reset Zoom"
              >
                100%
              </button>
            </div>
            
            {/* Transformation Controls */}
            <div className="flex items-center gap-2 ml-4 border-l pl-4">
              <label className="text-sm font-medium text-gray-700" title="Mathematical transformation to enhance visibility of small attention values">
                Transform:
              </label>
              <select
                value={transformMethod}
                onChange={(e) => setTransformMethod(e.target.value as typeof transformMethod)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                title="Choose a transformation to better visualize small attention values"
              >
                <option value="none" title="Linear scale - shows raw attention values">None</option>
                <option value="log" title="Natural logarithm - spreads out small values">Log (base e)</option>
                <option value="log10" title="Base-10 logarithm - useful for multiple orders of magnitude">Log₁₀</option>
                <option value="sqrt" title="Square root - moderate enhancement of small values">Square Root</option>
                <option value="power" title="Power 0.3 - strong enhancement of small values">Power (0.3)</option>
                <option value="power-extreme" title="Power 0.1 - extreme enhancement for tiny values">Power (0.1)</option>
                <option value="exclude-sink" title="Normalizes without first token to show other token differences">Exclude Sink</option>
              </select>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors ml-2"
              title="Close (Esc)"
            >
              <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content - Scrollable */}
        <div 
          ref={containerRef}
          className="flex-1 overflow-auto p-4"
          onWheel={handleWheel}
        >
          {renderError ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center p-8 bg-red-50 rounded-lg">
                <p className="text-red-700 mb-2">Error rendering attention matrix:</p>
                <p className="text-red-600 text-sm">{renderError}</p>
              </div>
            </div>
          ) : (
            <canvas 
              ref={canvasRef}
              onMouseMove={handleMouseMove}
              onMouseLeave={() => setHoveredCell(null)}
              className="border border-gray-300"
            />
          )}
        </div>

        {/* Hover tooltip */}
        {hoveredCell && (
          <div 
            className="absolute bg-gray-900 text-white p-2 rounded text-xs pointer-events-none z-20"
            style={{
              bottom: '100px',
              right: '20px'
            }}
          >
            <div>Weight: {hoveredCell.value.toFixed(4)}</div>
            <div>From [{hoveredCell.row}]: {tokens[hoveredCell.row]?.substring(0, 20)}</div>
            <div>To [{hoveredCell.col}]: {tokens[hoveredCell.col]?.substring(0, 20)}</div>
          </div>
        )}

        {/* Instructions */}
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur p-2 rounded-lg shadow text-xs text-gray-600">
          <div>Ctrl/Cmd + Scroll: Zoom | Scroll: Navigate | Hover: See values | Esc: Close</div>
          <div>Cell size: {(5 * zoomLevel).toFixed(1)}px | Zoom: {Math.round(zoomLevel * 100)}%</div>
        </div>
      </div>
    </div>
  );
}