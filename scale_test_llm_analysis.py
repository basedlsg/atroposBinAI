#!/usr/bin/env python3
"""
Comprehensive Scale Testing for LLM Society Simulation
Tests different agent counts, LLM providers, and scenarios to gather performance data
"""

import os
import sys
import asyncio
import time
import json
import statistics
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.append('src')
sys.path.append('.')

from llm_integration import LLMManager, LLMProvider, LLMRequest, create_agent_prompt

def setup_environment():
    """Setup environment variables for testing"""
    api_keys = {
        "OPENAI_API_KEY": "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",
        "GEMINI_API_KEY": "AIzaSyAqko3NqGS-GtXhzm8LeiZ3xUEyo_XIqLo",
        "LLAMA_API_KEY": "LLM|1469017110898899|mJOyVVo1xc4vbUj6y1Wj-svovnE"
    }
    
    for key, value in api_keys.items():
        os.environ[key] = value

class ScaleTestResults:
    """Container for scale test results"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, test_config, performance_data, llm_stats, agent_responses):
        """Add a test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_config': test_config,
            'performance': performance_data,
            'llm_stats': llm_stats,
            'sample_responses': agent_responses[:3],  # First 3 responses for quality analysis
            'success': performance_data.get('success', False)
        }
        self.results.append(result)
    
    def save_results(self, filename='scale_test_results.json'):
        """Save results to JSON file"""
        output = {
            'test_session': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_tests': len(self.results)
            },
            'results': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"📁 Results saved to {filename}")

async def generate_diverse_agent_contexts(num_agents):
    """Generate diverse agent contexts for testing"""
    
    agent_types = ['farmer', 'trader', 'craftsman', 'leader', 'scholar', 'warrior', 'healer', 'explorer']
    personality_traits = [
        ['hardworking', 'peaceful', 'generous'],
        ['ambitious', 'social', 'competitive'], 
        ['creative', 'patient', 'detail_oriented'],
        ['strategic', 'diplomatic', 'charismatic'],
        ['curious', 'analytical', 'wise'],
        ['brave', 'loyal', 'protective'],
        ['compassionate', 'intuitive', 'nurturing'],
        ['adventurous', 'independent', 'resourceful']
    ]
    
    goals_by_type = {
        'farmer': ['grow_crops', 'help_community', 'achieve_sustainability'],
        'trader': ['accumulate_wealth', 'expand_network', 'find_rare_goods'],
        'craftsman': ['create_art', 'master_craft', 'teach_skills'],
        'leader': ['unite_community', 'resolve_conflicts', 'build_prosperity'],
        'scholar': ['seek_knowledge', 'preserve_wisdom', 'educate_others'],
        'warrior': ['protect_community', 'train_others', 'maintain_order'],
        'healer': ['help_sick', 'research_medicine', 'prevent_disease'],
        'explorer': ['discover_lands', 'map_territory', 'find_resources']
    }
    
    contexts = []
    
    for i in range(num_agents):
        agent_type = agent_types[i % len(agent_types)]
        
        context = {
            'id': f'{agent_type}_{i:03d}',
            'agent_type': agent_type,
            'energy': 0.3 + (i % 7) * 0.1,  # Vary energy 0.3-0.9
            'happiness': 0.2 + (i % 8) * 0.1,  # Vary happiness 0.2-0.9
            'resources': {
                'food': 10 + (i % 50),
                'currency': 50 + (i % 500), 
                'materials': 5 + (i % 40)
            },
            'personality_traits': personality_traits[i % len(personality_traits)],
            'goals': goals_by_type[agent_type],
            'nearby_agents': [
                {'type': agent_types[(i+1) % len(agent_types)], 'distance': 5.0 + (i % 20)},
                {'type': agent_types[(i+2) % len(agent_types)], 'distance': 8.0 + (i % 15)}
            ],
            'state': ['idle', 'working', 'socializing', 'resting'][i % 4],
            'recent_actions': ['explored_area', 'traded_goods', 'helped_neighbor', 'gathered_resources'][i % 4]
        }
        
        contexts.append(context)
    
    return contexts

async def run_scale_test(provider, model, num_agents, num_steps, test_name=""):
    """Run a scale test with specified parameters"""
    
    print(f"\n🧪 Scale Test: {test_name}")
    print(f"   Provider: {provider.value}, Model: {model}")
    print(f"   Agents: {num_agents}, Steps: {num_steps}")
    print(f"   Total LLM requests: {num_agents * num_steps}")
    
    # Initialize LLM manager
    llm_manager = LLMManager(provider=provider, model=model)
    
    if llm_manager.provider == LLMProvider.NONE:
        print(f"   ❌ {provider.value} not available, skipping test")
        return None
    
    # Generate agent contexts
    agent_contexts = await generate_diverse_agent_contexts(num_agents)
    
    # Performance tracking
    start_time = time.time()
    successful_requests = 0
    failed_requests = 0
    response_times = []
    agent_responses = []
    
    print(f"   🚀 Starting simulation...")
    
    try:
        # Simulate multiple steps
        for step in range(num_steps):
            step_start = time.time()
            step_responses = []
            
            print(f"      Step {step + 1}/{num_steps}...", end="")
            
            # Process all agents in this step
            for i, context in enumerate(agent_contexts):
                # Update context for this step
                context.update({
                    'step': step,
                    'simulation_time': step * 1.0,  # Each step = 1 time unit
                })
                
                # Create prompt
                prompt = create_agent_prompt(context)
                request = LLMRequest(
                    agent_id=context['id'],
                    prompt=prompt,
                    context=context,
                    max_tokens=120,
                    temperature=0.7
                )
                
                # Get LLM response
                request_start = time.time()
                response = await llm_manager.get_response(request)
                request_end = time.time()
                
                response_time = request_end - request_start
                response_times.append(response_time)
                
                if response.success:
                    successful_requests += 1
                    step_responses.append({
                        'agent_id': context['id'],
                        'agent_type': context['agent_type'],
                        'response': response.response,
                        'response_time': response_time
                    })
                else:
                    failed_requests += 1
                    print(f"\n         ❌ Agent {i} failed: {response.error}")
            
            step_end = time.time()
            step_time = step_end - step_start
            
            print(f" ✅ ({step_time:.2f}s, {len(step_responses)} responses)")
            
            # Store responses from first step for analysis
            if step == 0:
                agent_responses = step_responses
            
            # Small delay between steps to avoid rate limiting
            if step < num_steps - 1:
                await asyncio.sleep(0.1)
    
    except Exception as e:
        print(f"\n   ❌ Test failed with error: {e}")
        return None
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate performance metrics
    total_requests = num_agents * num_steps
    success_rate = successful_requests / total_requests if total_requests > 0 else 0
    requests_per_second = successful_requests / total_time if total_time > 0 else 0
    avg_response_time = statistics.mean(response_times) if response_times else 0
    median_response_time = statistics.median(response_times) if response_times else 0
    
    # Get LLM stats
    llm_stats = llm_manager.get_stats()
    
    # Performance data
    performance_data = {
        'success': True,
        'total_time': total_time,
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'success_rate': success_rate,
        'requests_per_second': requests_per_second,
        'avg_response_time': avg_response_time,
        'median_response_time': median_response_time,
        'min_response_time': min(response_times) if response_times else 0,
        'max_response_time': max(response_times) if response_times else 0
    }
    
    # Print results
    print(f"   📊 Results:")
    print(f"      Total time: {total_time:.2f}s")
    print(f"      Requests/sec: {requests_per_second:.2f}")
    print(f"      Success rate: {success_rate:.1%}")
    print(f"      Avg response time: {avg_response_time:.3f}s")
    print(f"      Cache hit rate: {llm_stats.get('cache_rate', 'N/A')}")
    
    return {
        'test_config': {
            'provider': provider.value,
            'model': model,
            'num_agents': num_agents,
            'num_steps': num_steps,
            'test_name': test_name
        },
        'performance': performance_data,
        'llm_stats': llm_stats,
        'agent_responses': agent_responses
    }

async def run_comprehensive_scale_tests():
    """Run comprehensive scale tests across different configurations"""
    
    print("🚀 Comprehensive LLM Scale Testing")
    print("=" * 60)
    
    results = ScaleTestResults()
    
    # Test configurations: (provider, model, agents, steps, test_name)
    test_configs = [
        # Small scale tests
        (LLMProvider.OPENAI, "gpt-3.5-turbo", 5, 5, "OpenAI Small Scale"),
        (LLMProvider.GEMINI, "gemini-1.5-flash", 5, 5, "Gemini Small Scale"),
        (LLMProvider.MOCK, "mock", 5, 5, "Mock Baseline Small"),
        
        # Medium scale tests  
        (LLMProvider.OPENAI, "gpt-3.5-turbo", 15, 10, "OpenAI Medium Scale"),
        (LLMProvider.GEMINI, "gemini-1.5-flash", 15, 10, "Gemini Medium Scale"),
        (LLMProvider.MOCK, "mock", 25, 20, "Mock Baseline Medium"),
        
        # Large scale tests
        (LLMProvider.OPENAI, "gpt-3.5-turbo", 25, 15, "OpenAI Large Scale"),
        (LLMProvider.GEMINI, "gemini-1.5-flash", 25, 15, "Gemini Large Scale"),
        (LLMProvider.MOCK, "mock", 50, 30, "Mock Baseline Large"),
        
        # Stress tests
        (LLMProvider.OPENAI, "gpt-3.5-turbo", 50, 10, "OpenAI Stress Test"),
        (LLMProvider.GEMINI, "gemini-1.5-flash", 50, 10, "Gemini Stress Test"),
        
        # Llama tests (will fallback if auth fails)
        (LLMProvider.LLAMA, "llama3.1-70b-instruct", 5, 5, "Llama Small Scale"),
        (LLMProvider.LLAMA, "llama3.1-70b-instruct", 15, 10, "Llama Medium Scale"),
    ]
    
    total_tests = len(test_configs)
    
    for i, (provider, model, agents, steps, test_name) in enumerate(test_configs):
        print(f"\n{'='*60}")
        print(f"Test {i+1}/{total_tests}: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = await run_scale_test(provider, model, agents, steps, test_name)
            
            if result:
                results.add_result(
                    result['test_config'],
                    result['performance'], 
                    result['llm_stats'],
                    result['agent_responses']
                )
                print(f"✅ Test completed successfully")
            else:
                print(f"❌ Test failed or skipped")
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        
        # Delay between tests to avoid rate limiting
        if i < total_tests - 1:
            print("⏳ Waiting 30 seconds before next test...")
            await asyncio.sleep(30)
    
    # Save results
    results.save_results()
    
    return results

def analyze_scale_test_results(results):
    """Analyze scale test results and provide insights"""
    
    print(f"\n📊 SCALE TEST ANALYSIS")
    print("=" * 60)
    
    if not results.results:
        print("❌ No results to analyze")
        return
    
    # Group results by provider
    by_provider = {}
    for result in results.results:
        if result['success']:
            provider = result['test_config']['provider']
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(result)
    
    print(f"📈 Performance Summary by Provider:")
    print("-" * 40)
    
    for provider, provider_results in by_provider.items():
        if not provider_results:
            continue
            
        # Calculate averages
        avg_rps = statistics.mean([r['performance']['requests_per_second'] for r in provider_results])
        avg_response_time = statistics.mean([r['performance']['avg_response_time'] for r in provider_results])
        avg_success_rate = statistics.mean([r['performance']['success_rate'] for r in provider_results])
        
        # Find best performance
        best_rps = max([r['performance']['requests_per_second'] for r in provider_results])
        
        print(f"\n{provider.upper()}:")
        print(f"  Average RPS: {avg_rps:.2f}")
        print(f"  Best RPS: {best_rps:.2f}")
        print(f"  Avg Response Time: {avg_response_time:.3f}s")
        print(f"  Success Rate: {avg_success_rate:.1%}")
        print(f"  Tests Completed: {len(provider_results)}")
    
    # Scale analysis
    print(f"\n📏 Scale Analysis:")
    print("-" * 40)
    
    scale_ranges = {
        'Small (≤10 agents)': lambda r: r['test_config']['num_agents'] <= 10,
        'Medium (11-25 agents)': lambda r: 11 <= r['test_config']['num_agents'] <= 25,
        'Large (26-50 agents)': lambda r: 26 <= r['test_config']['num_agents'] <= 50,
        'Stress (50+ agents)': lambda r: r['test_config']['num_agents'] > 50
    }
    
    for scale_name, scale_filter in scale_ranges.items():
        scale_results = [r for r in results.results if r['success'] and scale_filter(r)]
        
        if scale_results:
            avg_rps = statistics.mean([r['performance']['requests_per_second'] for r in scale_results])
            best_provider = max(scale_results, key=lambda r: r['performance']['requests_per_second'])
            
            print(f"\n{scale_name}:")
            print(f"  Average RPS: {avg_rps:.2f}")
            print(f"  Best: {best_provider['test_config']['provider']} ({best_provider['performance']['requests_per_second']:.2f} RPS)")
    
    # Cost analysis
    print(f"\n💰 Cost Analysis (Estimated):")
    print("-" * 40)
    
    cost_per_1m_tokens = {
        'openai': 4.00,
        'gemini': 0.50,
        'llama': 0.20,
        'mock': 0.00
    }
    
    tokens_per_request = 150  # Estimated average
    
    for provider, provider_results in by_provider.items():
        if provider in cost_per_1m_tokens and provider_results:
            avg_rps = statistics.mean([r['performance']['requests_per_second'] for r in provider_results])
            
            # Cost for 1000 requests
            cost_1k_requests = (1000 * tokens_per_request / 1_000_000) * cost_per_1m_tokens[provider]
            
            # Cost per hour at average RPS
            requests_per_hour = avg_rps * 3600
            cost_per_hour = (requests_per_hour * tokens_per_request / 1_000_000) * cost_per_1m_tokens[provider]
            
            print(f"\n{provider.upper()}:")
            print(f"  Cost per 1K requests: ${cost_1k_requests:.3f}")
            print(f"  Cost per hour (avg RPS): ${cost_per_hour:.2f}")
    
    # Quality analysis
    print(f"\n🧠 Response Quality Analysis:")
    print("-" * 40)
    
    for provider, provider_results in by_provider.items():
        if provider == 'mock':
            continue
            
        # Analyze response lengths and complexity
        all_responses = []
        for result in provider_results:
            for response in result['sample_responses']:
                all_responses.append(response['response'])
        
        if all_responses:
            avg_length = statistics.mean([len(r) for r in all_responses])
            
            # Count strategic keywords
            strategic_keywords = ['plan', 'strategy', 'because', 'therefore', 'consider', 'analyze', 'decide']
            strategic_count = sum(1 for response in all_responses 
                                for keyword in strategic_keywords 
                                if keyword.lower() in response.lower())
            
            print(f"\n{provider.upper()}:")
            print(f"  Avg response length: {avg_length:.0f} chars")
            print(f"  Strategic thinking indicators: {strategic_count}")
            print(f"  Sample response: {all_responses[0][:100]}...")

def generate_llama_integration_recommendations(results):
    """Generate recommendations for Llama API integration based on test results"""
    
    print(f"\n🦙 LLAMA API INTEGRATION RECOMMENDATIONS")
    print("=" * 60)
    
    # Check if Llama tests were successful
    llama_results = [r for r in results.results if r['test_config']['provider'] == 'llama' and r['success']]
    
    if llama_results:
        print("✅ Llama API tests were successful!")
        
        avg_rps = statistics.mean([r['performance']['requests_per_second'] for r in llama_results])
        avg_response_time = statistics.mean([r['performance']['avg_response_time'] for r in llama_results])
        
        print(f"📊 Llama Performance:")
        print(f"   Average RPS: {avg_rps:.2f}")
        print(f"   Average Response Time: {avg_response_time:.3f}s")
        
        # Compare with other providers
        openai_results = [r for r in results.results if r['test_config']['provider'] == 'openai' and r['success']]
        gemini_results = [r for r in results.results if r['test_config']['provider'] == 'gemini' and r['success']]
        
        if openai_results:
            openai_avg_rps = statistics.mean([r['performance']['requests_per_second'] for r in openai_results])
            print(f"📈 vs OpenAI: {avg_rps/openai_avg_rps:.1f}x performance")
        
        if gemini_results:
            gemini_avg_rps = statistics.mean([r['performance']['requests_per_second'] for r in gemini_results])
            print(f"📈 vs Gemini: {avg_rps/gemini_avg_rps:.1f}x performance")
        
        print(f"\n🎯 Recommendations:")
        print("   1. ✅ Deploy Llama as primary provider (lowest cost)")
        print("   2. ✅ Use OpenAI for complex reasoning tasks")
        print("   3. ✅ Use Gemini for balanced performance/cost")
        print("   4. ✅ Implement intelligent provider switching")
        
    else:
        print("❌ Llama API tests failed - debugging needed")
        
        print(f"\n🔧 Debug Steps:")
        print("   1. 🔍 Verify API key format")
        print("   2. 🔍 Test different endpoints")
        print("   3. 🔍 Try third-party providers (Together AI, Groq)")
        print("   4. 🔍 Check authentication headers")
        
        print(f"\n🔄 Alternative Approaches:")
        print("   1. 🌐 Use Together AI for Llama access")
        print("   2. 🌐 Use Groq for high-speed Llama inference")
        print("   3. 🌐 Use Replicate for Llama API access")
        print("   4. 🏠 Self-host Llama with vLLM/TGI")
        
        # Show working providers as alternatives
        working_providers = [r['test_config']['provider'] for r in results.results if r['success']]
        working_providers = list(set(working_providers))
        
        if working_providers:
            print(f"\n✅ Working Providers (use while debugging Llama):")
            for provider in working_providers:
                if provider != 'mock':
                    provider_results = [r for r in results.results if r['test_config']['provider'] == provider and r['success']]
                    if provider_results:
                        avg_rps = statistics.mean([r['performance']['requests_per_second'] for r in provider_results])
                        print(f"   • {provider.upper()}: {avg_rps:.2f} RPS")

async def main():
    """Main function"""
    
    print("🧪 LLM Scale Testing & Analysis")
    print("=" * 60)
    print("This will test OpenAI, Gemini, and Llama at different scales")
    print("to determine optimal integration strategies.")
    print()
    
    # Setup environment
    setup_environment()
    
    # Run comprehensive tests
    results = await run_comprehensive_scale_tests()
    
    # Analyze results
    analyze_scale_test_results(results)
    
    # Generate Llama recommendations
    generate_llama_integration_recommendations(results)
    
    print(f"\n🎯 Scale Testing Complete!")
    print("=" * 60)
    print("✅ Performance data collected")
    print("✅ Cost analysis completed") 
    print("✅ Quality analysis finished")
    print("✅ Llama integration recommendations generated")
    print(f"📁 Detailed results saved to scale_test_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 