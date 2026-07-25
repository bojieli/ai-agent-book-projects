"""
Create animated bar chart race showing leaderboard evolution over time
"""
import pandas as pd
import numpy as np
from typing import List, Tuple
import json
import os


def prepare_animation_data(history_df: pd.DataFrame, top_n: int = 15) -> dict:
    """
    Prepare data for D3.js bar chart race animation.
    
    Args:
        history_df: DataFrame with columns: date, model, rating, rank
        top_n: Number of top models to show at each time point
        
    Returns:
        Dictionary with animation data
    """
    # Get all unique dates
    dates = sorted(history_df['date'].unique())
    if len(dates) == 0:
        return {
            'frames': [],
            'total_frames': 0,
            'top_n': top_n,
            'start_date': None,
            'end_date': None,
        }
    
    # For each date, get top N models
    frames = []
    for date in dates:
        date_data = history_df[history_df['date'] == date].nlargest(top_n, 'rating')
        
        frame = {
            'date': date.strftime('%Y-%m-%d'),
            'timestamp': int(date.timestamp()),
            'models': []
        }
        
        for rank, row in enumerate(date_data.itertuples(), 1):
            frame['models'].append({
                'rank': rank,
                'name': row.model,
                'rating': float(row.rating),
                'matches': int(row.matches),
                'wins': float(row.wins)
            })
        
        frames.append(frame)
    
    animation_data = {
        'frames': frames,
        'total_frames': len(frames),
        'top_n': top_n,
        'start_date': dates[0].strftime('%Y-%m-%d'),
        'end_date': dates[-1].strftime('%Y-%m-%d')
    }
    
    return animation_data


def generate_html_animation(animation_data: dict, output_path: str = "leaderboard_animation.html"):
    """
    Generate standalone HTML file with D3.js bar chart race animation.
    
    Args:
        animation_data: Dictionary from prepare_animation_data
        output_path: Path to save HTML file
    """
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Leaderboard Evolution</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        
        #container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        
        #date-display {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            color: #666;
            margin-bottom: 20px;
        }
        
        #chart {
            margin: 20px 0;
        }
        
        .bar {
            fill: steelblue;
            cursor: pointer;
            transition: fill 0.3s;
        }
        
        .bar:hover {
            fill: #4682b4;
        }
        
        .bar-label {
            font-size: 14px;
            fill: white;
            font-weight: bold;
        }
        
        .bar-value {
            font-size: 12px;
            fill: #333;
        }
        
        .rank-label {
            font-size: 18px;
            fill: #666;
            font-weight: bold;
        }
        
        #controls {
            text-align: center;
            margin-top: 30px;
        }
        
        button {
            padding: 10px 20px;
            margin: 0 5px;
            font-size: 16px;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            background: #4CAF50;
            color: white;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #45a049;
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        #progress-bar {
            width: 100%;
            height: 5px;
            background: #e0e0e0;
            margin-top: 20px;
            border-radius: 3px;
            overflow: hidden;
        }
        
        #progress {
            height: 100%;
            background: #4CAF50;
            width: 0%;
            transition: width 0.5s;
        }
        
        #speed-control {
            margin-top: 20px;
            text-align: center;
        }
        
        #speed-slider {
            width: 300px;
            margin: 0 10px;
        }
        
        .info-box {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div id="container">
        <h1>🏆 Model Leaderboard Evolution</h1>
        <div id="date-display">Loading...</div>
        <div id="chart"></div>
        <div id="controls">
            <button id="play-btn">▶ Play</button>
            <button id="pause-btn" disabled>⏸ Pause</button>
            <button id="reset-btn">↺ Reset</button>
        </div>
        <div id="progress-bar">
            <div id="progress"></div>
        </div>
        <div id="speed-control">
            <label>Speed: </label>
            <input type="range" id="speed-slider" min="1" max="10" value="5">
            <span id="speed-value">5x</span>
        </div>
        <div class="info-box">
            <strong>About:</strong> This animation shows the evolution of model rankings based on Elo ratings 
            calculated from Chatbot Arena voting data. Each frame represents a snapshot in time, 
            with models ranked by their current Elo rating. Bars show the rating value, 
            and the animation reveals how models compete and evolve over time.
        </div>
    </div>

    <script>
        const data = """ + json.dumps(animation_data, indent=2) + """;
        
        // Configuration
        const margin = {top: 20, right: 100, bottom: 40, left: 50};
        const width = 1100 - margin.left - margin.right;
        const height = 600 - margin.top - margin.bottom;
        const barHeight = height / data.top_n - 5;
        
        // Create SVG
        const svg = d3.select("#chart")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
        
        // Scales
        const xScale = d3.scaleLinear()
            .domain([0, d3.max(data.frames.flatMap(f => f.models.map(m => m.rating)))])
            .range([0, width - 200]);
        
        // Color scale
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10);
        
        // Animation state
        let currentFrame = 0;
        let isPlaying = false;
        let animationInterval = null;
        let animationSpeed = 500; // milliseconds per frame
        
        // Update speed based on slider
        d3.select("#speed-slider").on("input", function() {
            const speed = +this.value;
            animationSpeed = 1000 / speed;
            d3.select("#speed-value").text(`${speed}x`);
            if (isPlaying) {
                stopAnimation();
                startAnimation();
            }
        });
        
        function updateChart(frameIndex) {
            const frame = data.frames[frameIndex];
            
            // Update date display
            d3.select("#date-display").text(frame.date);
            
            // Update progress bar
            const progress = ((frameIndex + 1) / data.total_frames) * 100;
            d3.select("#progress").style("width", `${progress}%`);
            
            // Update max value for scale
            const maxRating = d3.max(frame.models, d => d.rating);
            xScale.domain([0, maxRating * 1.1]);
            
            // Bind data
            const bars = svg.selectAll(".bar-group")
                .data(frame.models, d => d.name);
            
            // Remove old bars
            bars.exit()
                .transition()
                .duration(animationSpeed * 0.8)
                .style("opacity", 0)
                .remove();
            
            // Add new bars
            const enter = bars.enter()
                .append("g")
                .attr("class", "bar-group")
                .style("opacity", 0);
            
            enter.append("rect")
                .attr("class", "bar")
                .attr("height", barHeight);
            
            enter.append("text")
                .attr("class", "bar-label")
                .attr("x", 10)
                .attr("y", barHeight / 2)
                .attr("dy", "0.35em");
            
            enter.append("text")
                .attr("class", "bar-value")
                .attr("y", barHeight / 2)
                .attr("dy", "0.35em");
            
            enter.append("text")
                .attr("class", "rank-label")
                .attr("x", -40)
                .attr("y", barHeight / 2)
                .attr("dy", "0.35em")
                .attr("text-anchor", "middle");
            
            // Update all bars
            const merged = enter.merge(bars);
            
            merged.transition()
                .duration(animationSpeed * 0.8)
                .style("opacity", 1)
                .attr("transform", (d, i) => `translate(0,${i * (barHeight + 5)})`);
            
            merged.select(".bar")
                .transition()
                .duration(animationSpeed * 0.8)
                .attr("width", d => xScale(d.rating))
                .attr("fill", d => colorScale(d.name));
            
            merged.select(".bar-label")
                .text(d => d.name);
            
            merged.select(".bar-value")
                .transition()
                .duration(animationSpeed * 0.8)
                .attr("x", d => xScale(d.rating) + 10)
                .text(d => `${Math.round(d.rating)} (${d.matches} matches)`);
            
            merged.select(".rank-label")
                .text(d => `#${d.rank}`);
        }
        
        function startAnimation() {
            if (currentFrame >= data.total_frames - 1) {
                currentFrame = 0;
            }
            
            isPlaying = true;
            d3.select("#play-btn").property("disabled", true);
            d3.select("#pause-btn").property("disabled", false);
            
            animationInterval = setInterval(() => {
                updateChart(currentFrame);
                currentFrame++;
                
                if (currentFrame >= data.total_frames) {
                    stopAnimation();
                    currentFrame = data.total_frames - 1;
                }
            }, animationSpeed);
        }
        
        function stopAnimation() {
            isPlaying = false;
            d3.select("#play-btn").property("disabled", false);
            d3.select("#pause-btn").property("disabled", true);
            
            if (animationInterval) {
                clearInterval(animationInterval);
                animationInterval = null;
            }
        }
        
        function resetAnimation() {
            stopAnimation();
            currentFrame = 0;
            updateChart(currentFrame);
            d3.select("#progress").style("width", "0%");
        }
        
        // Button handlers
        d3.select("#play-btn").on("click", startAnimation);
        d3.select("#pause-btn").on("click", stopAnimation);
        d3.select("#reset-btn").on("click", resetAnimation);
        
        // Initialize with first frame
        updateChart(0);
        
        // Auto-play on load
        setTimeout(startAnimation, 1000);
    </script>
</body>
</html>"""
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Generated animation HTML at: {output_path}")
    print(f"Open the file in a web browser to view the animation.")


def create_simple_animation(history_df: pd.DataFrame, output_path: str = "leaderboard_animation.html", top_n: int = 15):
    """
    Convenience function to create animation in one step.
    
    Args:
        history_df: DataFrame with rating history
        output_path: Path to save HTML file
        top_n: Number of top models to show
    """
    print("Preparing animation data...")
    animation_data = prepare_animation_data(history_df, top_n)
    
    print(f"Generating HTML animation with {animation_data['total_frames']} frames...")
    generate_html_animation(animation_data, output_path)
    
    return output_path

