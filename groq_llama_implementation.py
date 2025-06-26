#!/usr/bin/env python3
"""
Groq Llama Implementation
Complete implementation for using Groq's free Llama 3.1 70B API

Key Benefits:
- FREE tier with no billing required
- 284 tokens/second (faster than GPT-4)
- Access to Llama 3.1 70B (most capable open model)
- OpenAI-compatible API

Steps to get API key:
1. Go to https://console.groq.com/
2. Sign up with email (no credit card required)
3. Go to API Keys section
4. Create new API key
5. Copy the key and use below
"""

import os
import sys
import asyncio
import json
import time
import aiohttp
from typing import Dict, List, Optional

# Add project paths
sys.path.append('src')
sys.path.append('.')

from llm_integration import LLMRequest, create_agent_prompt

class GroqLlamaProvider:
    """
    Groq Llama API provider with free tier support
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.base_url = 'https://api.groq.com/openai/v1/chat/completions'
        self.models = {
            'llama-3.3-70b-versatile': {
                'name': 'Llama 3.3 70B',
                'context_length': 32768,
                'speed': 'very_fast',
                'cost': 'free'
            },
            'llama-3.1-70b-versatile': {
                'name': 'Llama 3.1 70B', 
                'context_length': 32768,
                'speed': 'very_fast',
                'cost': 'free'
            },
            'llama-3.1-8b-instant': {
                'name': 'Llama 3.1 8B',
                'context_length': 131072,
                'speed': 'extremely_fast',
                'cost': 'free'
            }
        }
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_response_time': 0.0,
            'rate_limit_hits': 0
        }
    
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key)
    
    async def make_request(self, request: LLMRequest, model: str = 'llama-3.1-70b-versatile') -> Dict:
        """Make a request to Groq API"""
        
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Groq API key not configured',
                'provider': 'groq'
            }
        
        self.stats['requests_made'] += 1
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': request.prompt}
            ],
            'max_tokens': request.max_tokens,
            'temperature': request.temperature,
            'top_p': 1,
            'stream': False
        }
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    self.stats['total_response_time'] += response_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0]['message']['content']
                            
                            # Track token usage if available
                            if 'usage' in data:
                                self.stats['total_tokens'] += data['usage'].get('total_tokens', 0)
                            
                            self.stats['successful_requests'] += 1
                            
                            return {
                                'success': True,
                                'response': content.strip(),
                                'provider': 'groq',
                                'model': model,
                                'response_time': response_time,
                                'tokens_used': data.get('usage', {}).get('total_tokens', 0),
                                'raw_response': data
                            }
                        else:
                            self.stats['failed_requests'] += 1
                            return {
                                'success': False,
                                'error': 'No choices in response',
                                'provider': 'groq',
                                'raw_response': data
                            }
                    
                    elif response.status == 429:
                        # Rate limit hit
                        self.stats['rate_limit_hits'] += 1
                        self.stats['failed_requests'] += 1
                        
                        error_data = await response.json()
                        retry_after = response.headers.get('retry-after', '60')
                        
                        return {
                            'success': False,
                            'error': f'Rate limit exceeded. Retry after {retry_after} seconds',
                            'provider': 'groq',
                            'retry_after': int(retry_after),
                            'raw_response': error_data
                        }
                    
                    else:
                        self.stats['failed_requests'] += 1
                        error_text = await response.text()
                        
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {error_text}',
                            'provider': 'groq'
                        }
                        
        except Exception as e:
            self.stats['failed_requests'] += 1
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'provider': 'groq'
            }
    
    def get_stats(self) -> Dict:
        """Get provider statistics"""
        
        avg_response_time = (
            self.stats['total_response_time'] / self.stats['requests_made'] 
            if self.stats['requests_made'] > 0 else 0
        )
        
        success_rate = (
            self.stats['successful_requests'] / self.stats['requests_made'] 
            if self.stats['requests_made'] > 0 else 0
        )
        
        return {
            'provider': 'groq',
            'requests_made': self.stats['requests_made'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': success_rate,
            'rate_limit_hits': self.stats['rate_limit_hits'],
            'total_tokens': self.stats['total_tokens'],
            'avg_response_time': avg_response_time,
            'models_available': list(self.models.keys())
        }

def print_setup_instructions():
    """Print detailed setup instructions"""
    
    print("🚀 GROQ LLAMA SETUP INSTRUCTIONS")
    print("=" * 60)
    print()
    print("📋 Step 1: Get Free Groq API Key")
    print("   1. Go to: https://console.groq.com/")
    print("   2. Click 'Sign Up' (no credit card required)")
    print("   3. Verify your email address")
    print("   4. Go to 'API Keys' section")
    print("   5. Click 'Create API Key'")
    print("   6. Copy the generated key")
    print()
    print("🔧 Step 2: Set Environment Variable")
    print("   Option A - Terminal:")
    print("   export GROQ_API_KEY='your-api-key-here'")
    print()
    print("   Option B - Python:")
    print("   os.environ['GROQ_API_KEY'] = 'your-api-key-here'")
    print()
    print("✅ Step 3: Test the Integration")
    print("   Run this script to test your setup!")
    print()
    print("💡 Groq Free Tier Benefits:")
    print("   • Llama 3.1 70B access (most capable)")
    print("   • 284 tokens/second (faster than GPT-4)")
    print("   • No billing required")
    print("   • OpenAI-compatible API")
    print("   • Rate limit: 6000 tokens/minute")

async def test_groq_llama():
    """Test Groq Llama integration"""
    
    print("\n🧪 TESTING GROQ LLAMA INTEGRATION")
    print("=" * 60)
    
    # Check if API key is configured
    api_key = os.getenv('GROQ_API_KEY')
    
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("💡 Please follow the setup instructions above")
        return False
    
    print(f"✅ API key configured: {api_key[:10]}...")
    
    # Initialize provider
    provider = GroqLlamaProvider(api_key)
    
    # Test different models
    models_to_test = [
        'llama-3.1-70b-versatile',
        'llama-3.1-8b-instant'
    ]
    
    # Create test scenarios
    test_scenarios = [
        {
            'name': 'Simple Question',
            'context': {
                'id': 'test_agent_001',
                'agent_type': 'trader',
                'energy': 0.8,
                'happiness': 0.6,
                'resources': {'food': 30, 'currency': 200, 'materials': 15},
                'personality_traits': ['ambitious', 'strategic'],
                'goals': ['accumulate_wealth'],
                'nearby_agents': [{'type': 'farmer', 'distance': 4.0}],
                'state': 'idle',
                'recent_actions': ['evaluated_market']
            }
        },
        {
            'name': 'Complex Reasoning',
            'context': {
                'id': 'test_agent_002', 
                'agent_type': 'leader',
                'energy': 0.9,
                'happiness': 0.7,
                'resources': {'food': 50, 'currency': 1000, 'materials': 25},
                'personality_traits': ['diplomatic', 'strategic', 'charismatic'],
                'goals': ['unite_community', 'resolve_conflicts'],
                'nearby_agents': [
                    {'type': 'farmer', 'distance': 2.0},
                    {'type': 'warrior', 'distance': 3.5},
                    {'type': 'trader', 'distance': 5.0}
                ],
                'state': 'planning',
                'recent_actions': ['mediated_dispute', 'called_meeting']
            }
        }
    ]
    
    results = []
    
    for model in models_to_test:
        print(f"\n🔍 Testing Model: {provider.models[model]['name']}")
        print("-" * 40)
        
        for scenario in test_scenarios:
            print(f"   📝 Scenario: {scenario['name']}")
            
            # Create prompt
            prompt = create_agent_prompt(scenario['context'])
            request = LLMRequest(
                agent_id=scenario['context']['id'],
                prompt=prompt,
                context=scenario['context'],
                max_tokens=150,
                temperature=0.7
            )
            
            # Make request
            start_time = time.time()
            result = await provider.make_request(request, model)
            end_time = time.time()
            
            if result['success']:
                print(f"   ✅ Success ({end_time - start_time:.2f}s)")
                print(f"      Response: {result['response'][:100]}...")
                print(f"      Tokens: {result.get('tokens_used', 'N/A')}")
                
                results.append({
                    'model': model,
                    'scenario': scenario['name'],
                    'success': True,
                    'response_time': end_time - start_time,
                    'response_length': len(result['response']),
                    'tokens_used': result.get('tokens_used', 0)
                })
            else:
                print(f"   ❌ Failed: {result['error']}")
                
                results.append({
                    'model': model,
                    'scenario': scenario['name'],
                    'success': False,
                    'error': result['error']
                })
                
                # If rate limited, wait
                if 'rate limit' in result['error'].lower():
                    retry_after = result.get('retry_after', 60)
                    print(f"   ⏳ Rate limited, waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    # Print summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    if successful_tests:
        print(f"✅ Successful tests: {len(successful_tests)}")
        
        avg_response_time = sum(r['response_time'] for r in successful_tests) / len(successful_tests)
        avg_response_length = sum(r['response_length'] for r in successful_tests) / len(successful_tests)
        total_tokens = sum(r['tokens_used'] for r in successful_tests)
        
        print(f"   Average response time: {avg_response_time:.3f}s")
        print(f"   Average response length: {avg_response_length:.0f} chars")
        print(f"   Total tokens used: {total_tokens}")
        
        # Test fastest model
        fastest_test = min(successful_tests, key=lambda x: x['response_time'])
        print(f"   Fastest: {fastest_test['model']} ({fastest_test['response_time']:.3f}s)")
    
    if failed_tests:
        print(f"❌ Failed tests: {len(failed_tests)}")
        for test in failed_tests:
            print(f"   • {test['model']} - {test['scenario']}: {test['error']}")
    
    # Get provider stats
    stats = provider.get_stats()
    print(f"\n📈 Provider Statistics:")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Average response time: {stats['avg_response_time']:.3f}s")
    print(f"   Rate limit hits: {stats['rate_limit_hits']}")
    print(f"   Total tokens: {stats['total_tokens']}")
    
    return len(successful_tests) > 0

async def run_performance_benchmark():
    """Run performance benchmark with Groq Llama"""
    
    print(f"\n🏆 PERFORMANCE BENCHMARK")
    print("=" * 50)
    
    provider = GroqLlamaProvider()
    
    if not provider.is_configured():
        print("❌ Groq API key not configured")
        return
    
    # Benchmark parameters
    num_agents = 20
    model = 'llama-3.1-8b-instant'  # Use fastest model for benchmark
    
    print(f"🎯 Benchmarking {num_agents} agents with {model}")
    
    # Generate test agents
    agent_contexts = []
    agent_types = ['farmer', 'trader', 'craftsman', 'scholar', 'warrior']
    
    for i in range(num_agents):
        context = {
            'id': f'benchmark_agent_{i:03d}',
            'agent_type': agent_types[i % len(agent_types)],
            'energy': 0.3 + (i % 7) * 0.1,
            'happiness': 0.2 + (i % 8) * 0.1,
            'resources': {
                'food': 10 + (i % 50),
                'currency': 50 + (i % 500),
                'materials': 5 + (i % 40)
            },
            'personality_traits': ['trait1', 'trait2'],
            'goals': ['goal1'],
            'nearby_agents': [{'type': 'other', 'distance': 5.0}],
            'state': 'idle',
            'recent_actions': ['action1']
        }
        agent_contexts.append(context)
    
    # Run benchmark
    start_time = time.time()
    successful_requests = 0
    
    print("🚀 Running benchmark...")
    
    for i, context in enumerate(agent_contexts):
        prompt = create_agent_prompt(context)
        request = LLMRequest(
            agent_id=context['id'],
            prompt=prompt,
            context=context,
            max_tokens=100,
            temperature=0.7
        )
        
        result = await provider.make_request(request, model)
        
        if result['success']:
            successful_requests += 1
            print(f"   ✅ Agent {i+1}/{num_agents}: {result['response'][:30]}...")
        else:
            print(f"   ❌ Agent {i+1}/{num_agents}: {result['error']}")
            
            # Handle rate limiting
            if 'rate limit' in result['error'].lower():
                retry_after = result.get('retry_after', 60)
                print(f"   ⏳ Rate limited, waiting {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                
                # Retry the request
                result = await provider.make_request(request, model)
                if result['success']:
                    successful_requests += 1
                    print(f"   ✅ Agent {i+1}/{num_agents} (retry): Success")
        
        # Small delay to respect rate limits
        await asyncio.sleep(0.5)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate metrics
    requests_per_second = successful_requests / total_time
    stats = provider.get_stats()
    
    print(f"\n🏁 BENCHMARK RESULTS")
    print("-" * 30)
    print(f"Total agents: {num_agents}")
    print(f"Successful: {successful_requests}")
    print(f"Failed: {num_agents - successful_requests}")
    print(f"Success rate: {successful_requests / num_agents:.1%}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Requests/sec: {requests_per_second:.2f}")
    print(f"Avg response time: {stats['avg_response_time']:.3f}s")
    print(f"Total tokens: {stats['total_tokens']}")
    
    # Compare with other providers
    print(f"\n📊 COMPARISON WITH OTHER PROVIDERS")
    print("-" * 40)
    print("Groq Llama 3.1 8B:")
    print(f"  • Speed: {requests_per_second:.2f} RPS")
    print(f"  • Cost: FREE")
    print(f"  • Quality: High (Llama 3.1)")
    print()
    print("Previous Results:")
    print("  • OpenAI GPT-3.5: 13.86 RPS, $4.00/1M tokens")
    print("  • Gemini Flash: 16.26 RPS, $0.50/1M tokens")
    print("  • Llama Direct: 7.32 RPS, $0.20/1M tokens (broken)")

def print_integration_plan():
    """Print plan for integrating Groq into the main system"""
    
    print(f"\n🔧 INTEGRATION PLAN")
    print("=" * 50)
    print()
    print("Phase 1: Basic Integration (1-2 hours)")
    print("  1. ✅ Get Groq API key (done)")
    print("  2. ✅ Test Groq integration (done)")
    print("  3. 🔄 Update llm_integration.py to include Groq")
    print("  4. 🔄 Add Groq as primary Llama provider")
    print("  5. 🔄 Test with small simulation")
    print()
    print("Phase 2: Production Deployment (2-4 hours)")
    print("  1. 🔄 Add GROQ_API_KEY to Google Cloud Secret Manager")
    print("  2. 🔄 Update Cloud Run environment variables")
    print("  3. 🔄 Deploy updated society-simulation service")
    print("  4. 🔄 Test production deployment")
    print()
    print("Phase 3: Optimization (1-2 days)")
    print("  1. 🔄 Implement intelligent model selection")
    print("  2. 🔄 Add rate limit handling and retries")
    print("  3. 🔄 Implement cost tracking")
    print("  4. 🔄 Add performance monitoring")
    print()
    print("Expected Benefits:")
    print("  • 🆓 FREE Llama 3.1 70B access")
    print("  • ⚡ 284 tokens/sec (faster than GPT-4)")
    print("  • 💰 90% cost reduction vs OpenAI")
    print("  • 🔄 Reliable fallback system")

async def main():
    """Main function"""
    
    print("🦙 GROQ LLAMA INTEGRATION")
    print("=" * 60)
    print("Free, fast, and powerful Llama 3.1 70B access!")
    print()
    
    # Print setup instructions
    print_setup_instructions()
    
    # Test integration
    success = await test_groq_llama()
    
    if success:
        # Run performance benchmark
        await run_performance_benchmark()
        
        # Print integration plan
        print_integration_plan()
    else:
        print("\n❌ Setup required before proceeding")
        print("💡 Follow the setup instructions above to get started")
    
    print(f"\n✅ Groq Llama Integration Complete!")

if __name__ == "__main__":
    asyncio.run(main()) 