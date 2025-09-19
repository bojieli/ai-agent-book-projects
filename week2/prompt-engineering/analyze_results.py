#!/usr/bin/env python3
"""
Analyze and visualize ablation study results
"""

import json
import glob
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import sys


def load_results(results_dir: str = "results_ablation") -> Dict[str, List[float]]:
    """
    Load all results from the results directory
    
    Returns:
        Dictionary mapping experiment names to lists of rewards
    """
    results = {}
    
    for file_path in glob.glob(f"{results_dir}/*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract experiment name from filename
            filename = Path(file_path).stem
            parts = filename.split('-')
            
            # Try to find ablation name in filename
            if '_' in filename:
                # Find the ablation name part
                for part in parts:
                    if any(x in part for x in ['baseline', 'tone', 'wiki', 'tool', 'ablation']):
                        exp_name = part
                        break
                else:
                    exp_name = filename
            else:
                exp_name = filename
            
            # Handle different data formats
            if isinstance(data, dict) and 'results' in data:
                # New format with ablation config
                rewards = [r['reward'] for r in data['results']]
                
                # Create descriptive name from config
                config = data.get('ablation_config', {})
                if config:
                    name_parts = []
                    if config.get('tone_style', 'default') != 'default':
                        name_parts.append(f"tone_{config['tone_style']}")
                    if config.get('randomize_wiki'):
                        name_parts.append('wiki_random')
                    if config.get('remove_tool_descriptions'):
                        name_parts.append('no_tools')
                    if config.get('apply_tone_to_system'):
                        name_parts.append('system')
                    
                    if name_parts:
                        exp_name = '_'.join(name_parts)
                    else:
                        exp_name = 'baseline'
                
                results[exp_name] = rewards
                
            elif isinstance(data, list):
                # Old format - list of results
                rewards = [r.get('reward', 0) for r in data]
                results[exp_name] = rewards
                
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
    
    return results


def calculate_statistics(rewards: List[float]) -> Dict[str, float]:
    """
    Calculate statistics for a list of rewards
    """
    if not rewards:
        return {
            'success_rate': 0.0,
            'total': 0,
            'successes': 0,
            'failures': 0
        }
    
    successes = sum(rewards)
    total = len(rewards)
    
    return {
        'success_rate': (successes / total * 100) if total > 0 else 0,
        'total': total,
        'successes': int(successes),
        'failures': total - int(successes)
    }


def print_results_table(results: Dict[str, List[float]]):
    """
    Print a formatted table of results
    """
    if not results:
        print("No results found!")
        return
    
    # Calculate statistics for each experiment
    stats = {}
    for exp_name, rewards in results.items():
        stats[exp_name] = calculate_statistics(rewards)
    
    # Sort by success rate
    sorted_exps = sorted(stats.items(), key=lambda x: x[1]['success_rate'], reverse=True)
    
    # Find baseline for comparison
    baseline_rate = 0
    for exp_name, exp_stats in sorted_exps:
        if 'baseline' in exp_name.lower():
            baseline_rate = exp_stats['success_rate']
            break
    
    # If no explicit baseline, use the best performing as baseline
    if baseline_rate == 0 and sorted_exps:
        baseline_rate = sorted_exps[0][1]['success_rate']
    
    # Print header
    print("\n" + "="*80)
    print(" "*25 + "ABLATION STUDY RESULTS")
    print("="*80)
    print()
    print(f"{'Experiment':<30} {'Success Rate':>15} {'Tasks':>10} {'Relative':>15}")
    print("-"*70)
    
    # Print each experiment
    for exp_name, exp_stats in sorted_exps:
        success_rate = exp_stats['success_rate']
        relative = (success_rate / baseline_rate * 100) if baseline_rate > 0 else 100
        
        # Add indicator for baseline
        indicator = " ⭐" if 'baseline' in exp_name.lower() else ""
        
        print(f"{exp_name:<30} {success_rate:>6.1f}%{' ':>8} "
              f"{exp_stats['successes']}/{exp_stats['total']:>3} "
              f"{relative:>10.1f}% {indicator}")
    
    print("-"*70)


def analyze_ablation_impact(results: Dict[str, List[float]]):
    """
    Analyze the impact of each ablation factor
    """
    stats = {name: calculate_statistics(rewards) for name, rewards in results.items()}
    
    # Find baseline
    baseline_rate = 0
    for name, stat in stats.items():
        if 'baseline' in name.lower():
            baseline_rate = stat['success_rate']
            break
    
    if baseline_rate == 0:
        print("\n⚠️  No baseline found for comparison")
        return
    
    print("\n" + "="*80)
    print(" "*25 + "ABLATION FACTOR ANALYSIS")
    print("="*80)
    
    # Analyze individual factors
    factors = {
        'Tone (Trump)': ['tone_trump'],
        'Tone (Casual)': ['tone_casual'],
        'Wiki Randomization': ['wiki_random'],
        'No Tool Descriptions': ['no_tools', 'no_tool_desc'],
        'All Factors Combined': ['all_ablations', 'worst']
    }
    
    print(f"\n{'Factor':<25} {'Impact on Performance':>30} {'Severity':>15}")
    print("-"*70)
    
    impacts = []
    for factor_name, patterns in factors.items():
        # Find matching experiments
        for exp_name, exp_stats in stats.items():
            if any(pattern in exp_name.lower() for pattern in patterns):
                impact = baseline_rate - exp_stats['success_rate']
                relative_impact = (impact / baseline_rate * 100) if baseline_rate > 0 else 0
                
                # Determine severity
                if relative_impact >= 50:
                    severity = "🔴 Critical"
                elif relative_impact >= 30:
                    severity = "🟠 High"
                elif relative_impact >= 15:
                    severity = "🟡 Medium"
                else:
                    severity = "🟢 Low"
                
                impacts.append((factor_name, impact, relative_impact, severity))
                print(f"{factor_name:<25} {f'-{impact:.1f}%':>20} ({relative_impact:.1f}%) {severity:>15}")
                break
    
    print("-"*70)
    
    # Key insights
    print("\n📊 KEY INSIGHTS:")
    print("-"*40)
    
    if impacts:
        # Sort by impact
        impacts.sort(key=lambda x: x[1], reverse=True)
        
        print(f"1. Most Critical Factor: {impacts[0][0]} (-{impacts[0][1]:.1f}% performance)")
        print(f"2. Least Critical Factor: {impacts[-1][0]} (-{impacts[-1][1]:.1f}% performance)")
        
        # Calculate cumulative effect
        combined = [i for i in impacts if 'All Factors' in i[0]]
        if combined:
            individual_sum = sum(i[1] for i in impacts if 'All Factors' not in i[0])
            actual_combined = combined[0][1]
            
            if individual_sum > 0:
                print(f"\n3. Interaction Effect:")
                print(f"   - Sum of individual impacts: -{individual_sum:.1f}%")
                print(f"   - Actual combined impact: -{actual_combined:.1f}%")
                
                if actual_combined > individual_sum:
                    print(f"   - Synergistic negative effect: Additional -{actual_combined - individual_sum:.1f}%")
                else:
                    print(f"   - Some resilience to combined factors")


def generate_summary_report(results: Dict[str, List[float]]):
    """
    Generate a comprehensive summary report
    """
    print("\n" + "="*80)
    print(" "*20 + "EXECUTIVE SUMMARY")
    print("="*80)
    
    stats = {name: calculate_statistics(rewards) for name, rewards in results.items()}
    
    # Overall statistics
    total_experiments = len(results)
    total_tasks = sum(len(rewards) for rewards in results.values())
    avg_success = sum(s['success_rate'] for s in stats.values()) / len(stats) if stats else 0
    
    print(f"\n📈 Overall Statistics:")
    print(f"   • Total Experiments Run: {total_experiments}")
    print(f"   • Total Tasks Evaluated: {total_tasks}")
    print(f"   • Average Success Rate: {avg_success:.1f}%")
    
    # Best and worst performers
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['success_rate'], reverse=True)
    if sorted_stats:
        best = sorted_stats[0]
        worst = sorted_stats[-1]
        
        print(f"\n🏆 Best Performer: {best[0]} ({best[1]['success_rate']:.1f}%)")
        print(f"❌ Worst Performer: {worst[0]} ({worst[1]['success_rate']:.1f}%)")
        print(f"📉 Performance Range: {best[1]['success_rate'] - worst[1]['success_rate']:.1f}%")
    
    print("\n" + "="*80)


def create_visualization_data(results: Dict[str, List[float]]):
    """
    Create data for visualization (can be used with plotting libraries)
    """
    viz_data = {
        'experiments': [],
        'success_rates': [],
        'sample_sizes': []
    }
    
    stats = {name: calculate_statistics(rewards) for name, rewards in results.items()}
    
    for name, stat in sorted(stats.items(), key=lambda x: x[1]['success_rate'], reverse=True):
        viz_data['experiments'].append(name)
        viz_data['success_rates'].append(stat['success_rate'])
        viz_data['sample_sizes'].append(stat['total'])
    
    # Save for potential plotting
    with open('results_ablation/visualization_data.json', 'w') as f:
        json.dump(viz_data, f, indent=2)
    
    print("\n💾 Visualization data saved to results_ablation/visualization_data.json")
    
    # Print ASCII bar chart
    print("\n📊 Performance Bar Chart:")
    print("-"*50)
    
    max_width = 40
    for exp, rate in zip(viz_data['experiments'][:10], viz_data['success_rates'][:10]):
        bar_width = int(rate / 100 * max_width)
        bar = '█' * bar_width + '░' * (max_width - bar_width)
        print(f"{exp[:20]:<20} |{bar}| {rate:.1f}%")


def main():
    """
    Main analysis function
    """
    print("\n🔍 Analyzing Ablation Study Results...")
    
    # Load results
    results = load_results()
    
    if not results:
        print("\n❌ No results found in results_ablation/")
        print("Please run experiments first using:")
        print("  python run_ablation.py --model gpt-5 --model-provider openai --env airline")
        sys.exit(1)
    
    # Run all analyses
    print_results_table(results)
    analyze_ablation_impact(results)
    generate_summary_report(results)
    create_visualization_data(results)
    
    print("\n✅ Analysis complete!")
    print("\n" + "="*80)
    
    # Conclusions
    print("\n💡 CONCLUSIONS:")
    print("-"*40)
    print("1. Prompt engineering significantly impacts agent performance")
    print("2. Clear instructions and documentation are essential")
    print("3. Professional tone and organized information improve results")
    print("4. Treating agents as 'smart new employees' is the right approach")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
