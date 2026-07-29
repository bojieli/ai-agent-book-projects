"""
Performance Metrics Module for Log Sanitization
"""

import time
import json
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """Store performance metrics for a single sanitization operation"""
    test_id: str
    conversation_id: str
    input_text_length: int
    input_tokens: int
    
    # Timing metrics
    prefill_time_ms: float  # Time to First Token (TTFT)
    output_time_ms: float
    total_time_ms: float
    
    # Token metrics
    output_tokens: int
    prefill_speed_tps: float  # tokens per second
    output_speed_tps: float
    
    # Sanitization results
    pii_items_found: int
    replacements_made: int
    sanitized_text_length: int
    
    # Timestamps
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class MetricsCollector:
    """Collect and aggregate performance metrics"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.metrics_file = output_dir / "performance_metrics.json"
        self.summary_file = output_dir / "performance_summary.json"
        self.metrics: List[PerformanceMetrics] = []
    
    def add_metric(self, metric: PerformanceMetrics):
        """Add a new metric to the collection"""
        self.metrics.append(metric)
    
    def calculate_summary(self) -> Dict:
        """Calculate summary statistics across all metrics"""
        if not self.metrics:
            return {"error": "No metrics collected"}
        
        # Collect all values for each metric
        prefill_times = [m.prefill_time_ms for m in self.metrics]
        output_times = [m.output_time_ms for m in self.metrics]
        total_times = [m.total_time_ms for m in self.metrics]
        
        input_tokens = [m.input_tokens for m in self.metrics]
        output_tokens = [m.output_tokens for m in self.metrics]
        
        prefill_speeds = [m.prefill_speed_tps for m in self.metrics]
        output_speeds = [m.output_speed_tps for m in self.metrics]
        
        pii_counts = [m.pii_items_found for m in self.metrics]
        replacements = [m.replacements_made for m in self.metrics]
        
        def calculate_stats(values: List[float]) -> Dict:
            """Calculate min, max, mean, median for a list of values"""
            if not values:
                return {"min": 0, "max": 0, "mean": 0, "median": 0}
            
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            return {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / n,
                "median": sorted_values[n // 2] if n % 2 == 1 else 
                         (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            }
        
        summary = {
            "total_conversations": len(self.metrics),
            "timestamp": datetime.now().isoformat(),
            
            "timing_metrics": {
                "prefill_time_ms": calculate_stats(prefill_times),
                "output_time_ms": calculate_stats(output_times),
                "total_time_ms": calculate_stats(total_times)
            },
            
            "token_metrics": {
                "input_tokens": calculate_stats(input_tokens),
                "output_tokens": calculate_stats(output_tokens),
                "total_input_tokens": sum(input_tokens),
                "total_output_tokens": sum(output_tokens)
            },
            
            "speed_metrics": {
                "prefill_speed_tps": calculate_stats(prefill_speeds),
                "output_speed_tps": calculate_stats(output_speeds)
            },
            
            "sanitization_metrics": {
                "pii_items_found": calculate_stats(pii_counts),
                "replacements_made": calculate_stats(replacements),
                "total_pii_found": sum(pii_counts),
                "total_replacements": sum(replacements)
            }
        }
        
        return summary
    
    def save_metrics(self):
        """Save all metrics and summary to files"""
        # Save detailed metrics
        metrics_data = [m.to_dict() for m in self.metrics]
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        # Save summary
        summary = self.calculate_summary()
        with open(self.summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Metrics saved to {self.metrics_file}")
        print(f"✅ Summary saved to {self.summary_file}")
    
    def print_summary(self):
        """Print a human-readable summary of metrics"""
        summary = self.calculate_summary()
        
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        
        print(f"\n📊 Total Conversations Processed: {summary['total_conversations']}")
        
        print("\n⏱️  Timing Metrics (milliseconds):")
        timing = summary['timing_metrics']
        print(f"   Prefill (TTFT): {timing['prefill_time_ms']['mean']:.2f} ms (median: {timing['prefill_time_ms']['median']:.2f})")
        print(f"   Output Time:    {timing['output_time_ms']['mean']:.2f} ms (median: {timing['output_time_ms']['median']:.2f})")
        print(f"   Total Time:     {timing['total_time_ms']['mean']:.2f} ms (median: {timing['total_time_ms']['median']:.2f})")
        
        print("\n📝 Token Metrics:")
        tokens = summary['token_metrics']
        print(f"   Average Input Tokens:  {tokens['input_tokens']['mean']:.1f}")
        print(f"   Average Output Tokens: {tokens['output_tokens']['mean']:.1f}")
        print(f"   Total Tokens Processed: {tokens['total_input_tokens'] + tokens['total_output_tokens']}")
        
        print("\n⚡ Speed Metrics (tokens/second):")
        speed = summary['speed_metrics']
        print(f"   Prefill Speed: {speed['prefill_speed_tps']['mean']:.1f} tok/s")
        print(f"   Output Speed:  {speed['output_speed_tps']['mean']:.1f} tok/s")
        
        print("\n🔒 Sanitization Results:")
        sanitization = summary['sanitization_metrics']
        print(f"   Total PII Items Found:     {sanitization['total_pii_found']}")
        print(f"   Total Replacements Made:   {sanitization['total_replacements']}")
        print(f"   Average PII per Conversation: {sanitization['pii_items_found']['mean']:.1f}")
        
        print("\n" + "=" * 60)
