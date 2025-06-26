#!/usr/bin/env python3
"""
STEP 2B: Full Scale Testing Suite
================================

Run comprehensive scale tests across multiple agent counts
to understand system behavior and performance characteristics.
"""

import asyncio
import json
from datetime import datetime
from step2_scale_testing import ScaleTestRunner

async def run_comprehensive_scale_tests():
    """Run the full scale testing suite"""
    
    print("🚀 COMPREHENSIVE SCALE TESTING SUITE")
    print("=" * 50)
    print("Testing enhanced intelligence system across multiple scales")
    print()
    
    runner = ScaleTestRunner()
    
    # Define test configurations
    test_configs = [
        (100, 5, "baseline_100_agents"),
        (250, 4, "small_250_agents"),
        (500, 3, "medium_500_agents"),
        (1000, 2, "large_1000_agents")
    ]
    
    results = {}
    
    for num_agents, num_steps, test_name in test_configs:
        print(f"\n🎯 Running {test_name}")
        print(f"   Configuration: {num_agents} agents, {num_steps} steps")
        
        try:
            result = await runner.run_scale_test(num_agents, num_steps, test_name)
            results[test_name] = result
            
            # Print key metrics
            perf = result['performance']
            behavior = result['behavioral_analysis']
            
            print(f"   📊 Performance Summary:")
            print(f"      • {perf['decisions_per_second']:.1f} decisions/second")
            print(f"      • {perf['avg_memory_mb']:.1f}MB average memory")
            print(f"      • {perf['avg_decision_time_ms']:.2f}ms per decision")
            
            print(f"   🧠 Behavioral Summary:")
            print(f"      • {behavior['decision_diversity']} different action types used")
            print(f"      • Most common action: {behavior['most_common_actions'][0][0] if behavior['most_common_actions'] else 'none'}")
            print(f"      • Final cooperation: {behavior['final_avg_cooperation']:.3f}")
            print(f"      • Final happiness: {behavior['final_avg_happiness']:.3f}")
            
            # Short pause between tests
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Test {test_name} failed: {e}")
            results[test_name] = {"error": str(e)}
    
    print("🎉 COMPREHENSIVE SCALE TESTING COMPLETE!")
    print(f"Total tests completed: {len([r for r in results.values() if 'error' not in r])}/{len(test_configs)}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(run_comprehensive_scale_tests())
