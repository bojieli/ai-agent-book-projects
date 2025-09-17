import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface AttentionPreviewProps {
  tokens: string[];
  attentionWeights: number[][];
  onClick: () => void;
}

export default function AttentionPreview({ tokens, attentionWeights, onClick }: AttentionPreviewProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !tokens?.length || !attentionWeights?.length) return;

    // Clear previous content
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Fixed preview size
    const previewSize = 800;
    const margin = 40;
    const innerSize = previewSize - 2 * margin;
    
    svg.attr('width', previewSize).attr('height', previewSize);

    const g = svg.append('g')
      .attr('transform', `translate(${margin},${margin})`);

    // Fixed 1:10 sampling rate
    const sampleRate = 10;
    
    // Sample tokens for preview
    const sampledIndices: number[] = [];
    for (let i = 0; i < tokens.length; i += sampleRate) {
      sampledIndices.push(i);
    }

    const numSamples = sampledIndices.length;
    const cellSize = innerSize / numSamples;

    // Color scale - calculate max efficiently
    let maxWeight = 0;
    for (let i = 0; i < attentionWeights.length; i++) {
      for (let j = 0; j < attentionWeights[i].length; j++) {
        if (attentionWeights[i][j] > maxWeight) {
          maxWeight = attentionWeights[i][j];
        }
      }
    }
    maxWeight = maxWeight || 1;
    
    // Apply log10 transformation for better visualization of small values
    const transformValue = (value: number) => {
      // Base-10 logarithm for intuitive order-of-magnitude understanding
      const log10Value = Math.log10(1 + value * 1000); // Scale up before log10
      const log10Max = Math.log10(1 + maxWeight * 1000);
      return log10Value / log10Max;
    };
    
    const colorScale = (value: number) => {
      const transformed = transformValue(value);
      return d3.interpolateViridis(transformed);
    };

    // Create sampled cells
    const cellData: any[] = [];
    sampledIndices.forEach((i, row) => {
      if (i < attentionWeights.length) {
        sampledIndices.forEach((j, col) => {
          if (j < attentionWeights[i].length) {
            cellData.push({
              row: row,
              col: col,
              value: attentionWeights[i][j]
            });
          }
        });
      }
    });

    // Render cells
    g.selectAll('.preview-cell')
      .data(cellData)
      .enter().append('rect')
      .attr('class', 'preview-cell')
      .attr('x', d => d.col * cellSize)
      .attr('y', d => d.row * cellSize)
      .attr('width', cellSize - 0.5)
      .attr('height', cellSize - 0.5)
      .attr('fill', (d: any) => colorScale(d.value))
      .style('stroke', '#fff')
      .style('stroke-width', 0.5);

    // Add overlay for click
    svg.append('rect')
      .attr('width', previewSize)
      .attr('height', previewSize)
      .attr('fill', 'transparent')
      .style('cursor', 'pointer')
      .on('click', onClick);

    // Add "Click to view" text overlay
    const textGroup = svg.append('g')
      .attr('transform', `translate(${previewSize / 2},${previewSize / 2})`);

    textGroup.append('rect')
      .attr('x', -100)
      .attr('y', -25)
      .attr('width', 200)
      .attr('height', 50)
      .attr('rx', 8)
      .style('fill', 'rgba(255, 255, 255, 0.95)')
      .style('stroke', '#333')
      .style('stroke-width', 2)
      .style('cursor', 'pointer')
      .style('opacity', 0)
      .on('click', onClick)
      .transition()
      .duration(500)
      .style('opacity', 1);

    textGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('alignment-baseline', 'middle')
      .style('font-size', '18px')
      .style('font-weight', 'bold')
      .style('fill', '#333')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .text('Click to View Full')
      .transition()
      .duration(500)
      .style('opacity', 1);

    // Show matrix size info
    svg.append('text')
      .attr('x', previewSize / 2)
      .attr('y', previewSize - 10)
      .attr('text-anchor', 'middle')
      .style('font-size', '14px')
      .style('fill', '#666')
      .text(`${tokens.length} × ${Math.min(tokens.length, attentionWeights.length)} tokens`);

    // Always show sampling info
    svg.append('text')
      .attr('x', previewSize / 2)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .style('font-size', '13px')
      .style('fill', '#999')
      .text(`Preview (1:${sampleRate} sampling)`);

  }, [tokens, attentionWeights, onClick]);

  return (
    <div className="inline-block">
      <svg 
        ref={svgRef} 
        className="border border-gray-300 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
      ></svg>
    </div>
  );
}
