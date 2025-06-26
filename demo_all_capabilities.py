#!/usr/bin/env python3
"""
Demonstration Script - All LLM Integration Capabilities
Shows the complete system working with real APIs
"""

import os
import json
import time
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section"""
    print(f"\n📋 {title}")
    print(f"{'-'*40}")

def demo_spatial_reasoning():
    """Demonstrate the spatial reasoning system"""
    print_section("Spatial Reasoning with Gemini API")
    
    try:
        # Import and run the spatial reasoning system
        from real_gemini_spatial_system import main as run_spatial_system
        print("🚀 Running spatial reasoning simulation...")
        run_spatial_system()
        print("✅ Spatial reasoning demonstration completed!")
        return True
    except Exception as e:
        print(f"❌ Spatial reasoning failed: {e}")
        return False

def demo_comprehensive_testing():
    """Demonstrate comprehensive testing"""
    print_section("Comprehensive Gemini Testing")
    
    try:
        # Import and run the test suite
        from test_gemini_integration import main as run_tests
        print("🧪 Running comprehensive test suite...")
        run_tests()
        print("✅ Comprehensive testing completed!")
        return True
    except Exception as e:
        print(f"❌ Comprehensive testing failed: {e}")
        return False

def demo_llm_comparison():
    """Demonstrate LLM comparison"""
    print_section("LLM Provider Comparison")
    
    try:
        # Import and run the comparison
        from llm_comparison_analysis import main as run_comparison
        print("🔬 Running LLM comparison analysis...")
        run_comparison()
        print("✅ LLM comparison completed!")
        return True
    except Exception as e:
        print(f"❌ LLM comparison failed: {e}")
        return False

def show_results_summary():
    """Show summary of all results"""
    print_section("Results Summary")
    
    results_files = [
        ("real_gemini_spatial_results.json", "Spatial Reasoning Results"),
        ("gemini_test_results.json", "Comprehensive Test Results"),
        ("llm_comparison_results.json", "LLM Comparison Results")
    ]
    
    for filename, description in results_files:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            print(f"\n📊 {description}:")
            
            if "metrics" in data:
                metrics = data["metrics"]
                print(f"  Total Decisions: {metrics.get('total_decisions', 'N/A')}")
                print(f"  Success Rate: {metrics.get('successful_decisions', 0)/metrics.get('total_decisions', 1)*100:.1f}%")
                print(f"  Avg Response Time: {metrics.get('average_response_time', 0):.3f}s")
            
            elif "total_tests" in data:
                print(f"  Total Tests: {data['total_tests']}")
                print(f"  Success Rate: {data['success_rate']*100:.1f}%")
                print(f"  Avg Response Time: {data['average_response_time']:.3f}s")
                print(f"  Avg Improvement: {data['average_improvement']:.2f} units")
            
            elif "provider_metrics" in data:
                print(f"  Providers Tested: {len(data['provider_metrics'])}")
                best = data.get('best_performance', {})
                if best:
                    print(f"  Best Performer: {best.get('provider', 'N/A')}")
                    print(f"  Best Score: {best.get('score', 0):.3f}")
            
        except FileNotFoundError:
            print(f"  ❌ {filename} not found")
        except Exception as e:
            print(f"  ❌ Error reading {filename}: {e}")

def show_visualization_info():
    """Show information about the visualization"""
    print_section("3D Visualization")
    
    viz_file = "visualization/gemini_visualization.html"
    if os.path.exists(viz_file):
        print("✅ 3D visualization available!")
        print(f"📁 File: {viz_file}")
        print("🌐 Open in browser to view interactive 3D environment")
        print("🎮 Features:")
        print("  - Real-time 3D agent movement")
        print("  - Interactive camera controls")
        print("  - Live performance metrics")
        print("  - Performance charts by difficulty")
        print("  - Multi-provider comparison")
    else:
        print("❌ Visualization file not found")

def show_api_status():
    """Show API configuration status"""
    print_section("API Configuration Status")
    
    apis = [
        ("GEMINI_API_KEY", "Google Gemini"),
        ("OPENAI_API_KEY", "OpenAI GPT")
    ]
    
    for env_var, provider in apis:
        api_key = os.getenv(env_var)
        if api_key:
            print(f"✅ {provider}: Configured ({api_key[:20]}...)")
        else:
            print(f"❌ {provider}: Not configured")

def main():
    """Main demonstration function"""
    print_header("LLM Integration System - Complete Demonstration")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show API status
    show_api_status()
    
    # Run demonstrations
    demonstrations = [
        ("Spatial Reasoning System", demo_spatial_reasoning),
        ("Comprehensive Testing", demo_comprehensive_testing),
        ("LLM Comparison Analysis", demo_llm_comparison)
    ]
    
    results = {}
    for name, demo_func in demonstrations:
        print(f"\n🎬 Running {name}...")
        try:
            results[name] = demo_func()
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results[name] = False
    
    # Show results summary
    show_results_summary()
    
    # Show visualization info
    show_visualization_info()
    
    # Final summary
    print_header("Demonstration Summary")
    
    successful_demos = sum(results.values())
    total_demos = len(results)
    
    print(f"🎯 Overall Success Rate: {successful_demos}/{total_demos} ({successful_demos/total_demos*100:.1f}%)")
    
    for name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\n🚀 Key Achievements:")
    print(f"  - Real LLM API integration (Gemini + OpenAI)")
    print(f"  - 3D spatial reasoning with live agents")
    print(f"  - Comprehensive testing framework")
    print(f"  - Performance comparison analysis")
    print(f"  - Interactive 3D visualization")
    print(f"  - Cost and efficiency analysis")
    
    print(f"\n📁 Generated Files:")
    files = [
        "real_gemini_spatial_results.json",
        "gemini_test_results.json", 
        "llm_comparison_results.json",
        "visualization/gemini_visualization.html"
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (not found)")
    
    print(f"\n🎉 Demonstration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📖 See COMPREHENSIVE_LLM_INTEGRATION_SUMMARY.md for detailed documentation")

if __name__ == "__main__":
    main() 