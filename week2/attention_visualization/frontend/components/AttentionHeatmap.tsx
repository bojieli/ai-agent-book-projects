import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface AttentionHeatmapProps {
  tokens: string[];
  attentionWeights: number[][];
}

export default function AttentionHeatmap({ tokens, attentionWeights }: AttentionHeatmapProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !tokens.length || !attentionWeights.length) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const margin = { top: 100, right: 50, bottom: 50, left: 100 };
    const cellSize = 20;
    const width = tokens.length * cellSize + margin.left + margin.right;
    const height = Math.min(tokens.length, attentionWeights.length) * cellSize + margin.top + margin.bottom;

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Color scale
    const colorScale = d3.scaleSequential(d3.interpolateViridis)
      .domain([0, d3.max(attentionWeights.flat()) || 1]);

    // Create heatmap cells
    const rows = g.selectAll('.row')
      .data(attentionWeights.slice(0, tokens.length))
      .enter().append('g')
      .attr('class', 'row')
      .attr('transform', (d, i) => `translate(0,${i * cellSize})`);

    rows.selectAll('.cell')
      .data((d, i) => d.slice(0, tokens.length).map((value, j) => ({
        row: i,
        col: j,
        value: value
      })))
      .enter().append('rect')
      .attr('class', 'cell attention-cell')
      .attr('x', d => d.col * cellSize)
      .attr('width', cellSize - 1)
      .attr('height', cellSize - 1)
      .attr('fill', d => colorScale(d.value))
      .on('mouseover', function(event, d: any) {
        // Show tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0,0,0,0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('z-index', '1000');

        tooltip.html(`
          <div>From: ${tokens[d.row] || 'N/A'}</div>
          <div>To: ${tokens[d.col] || 'N/A'}</div>
          <div>Weight: ${d.value.toFixed(4)}</div>
        `)
          .style('left', `${event.pageX + 10}px`)
          .style('top', `${event.pageY - 10}px`);
      })
      .on('mouseout', function() {
        d3.selectAll('.tooltip').remove();
      });

    // Add token labels on top
    g.selectAll('.col-label')
      .data(tokens)
      .enter().append('text')
      .attr('class', 'col-label')
      .attr('x', (d, i) => i * cellSize + cellSize / 2)
      .attr('y', -5)
      .attr('text-anchor', 'end')
      .attr('transform', (d, i) => `rotate(-65,${i * cellSize + cellSize / 2},-5)`)
      .style('font-size', '10px')
      .style('fill', '#333')
      .text(d => d.length > 15 ? d.substring(0, 15) + '...' : d);

    // Add token labels on left
    g.selectAll('.row-label')
      .data(tokens.slice(0, attentionWeights.length))
      .enter().append('text')
      .attr('class', 'row-label')
      .attr('x', -5)
      .attr('y', (d, i) => i * cellSize + cellSize / 2)
      .attr('text-anchor', 'end')
      .attr('alignment-baseline', 'middle')
      .style('font-size', '10px')
      .style('fill', '#333')
      .text(d => d.length > 15 ? d.substring(0, 15) + '...' : d);

    // Add color legend
    const legendWidth = 200;
    const legendHeight = 20;
    
    const legendScale = d3.scaleLinear()
      .domain([0, d3.max(attentionWeights.flat()) || 1])
      .range([0, legendWidth]);

    const legendAxis = d3.axisBottom(legendScale)
      .ticks(5)
      .tickFormat(d3.format('.2f'));

    const legend = svg.append('g')
      .attr('transform', `translate(${margin.left},${height - 30})`);

    // Create gradient for legend
    const gradientId = 'attention-gradient';
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', gradientId)
      .attr('x1', '0%')
      .attr('x2', '100%');

    const steps = 20;
    for (let i = 0; i <= steps; i++) {
      gradient.append('stop')
        .attr('offset', `${(i / steps) * 100}%`)
        .attr('stop-color', colorScale(i / steps * (d3.max(attentionWeights.flat()) || 1)));
    }

    legend.append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', `url(#${gradientId})`);

    legend.append('g')
      .attr('transform', `translate(0,${legendHeight})`)
      .call(legendAxis);

    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#333')
      .text('Attention Weight');

  }, [tokens, attentionWeights]);

  return (
    <div className="w-full overflow-x-auto">
      <svg ref={svgRef}></svg>
    </div>
  );
}
