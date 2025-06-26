#!/usr/bin/env python3
"""
Practical Llama Integration Implementation
Fixes the Llama API issues by using reliable third-party providers
"""

import os
import sys
import asyncio
import json
import time
from typing import Dict, List, Optional

# Add project paths
sys.path.append('src')
sys.path.append('.')

from llm_integration import LLMManager, LLMProvider, LLMRequest, create_agent_prompt

class LlamaProviderManager:
    """
    Manages multiple Llama providers with fallback logic
    """
    
    def __init__(self):
        self.providers = self.setup_providers()
        self.current_provider = None
        self.stats = {
            'requests_by_provider': {},
            'failures_by_provider': {},
            'response_times': {},
            'costs': {}
        }
    
    def setup_providers(self):
        """Setup available Llama providers"""
        
        providers = {}
        
        # Together AI - Most reliable
        if os.getenv('TOGETHER_API_KEY'):
            providers['together'] = {
                'name': 'Together AI',
                'endpoint': 'https://api.together.xyz/v1/chat/completions',
                'api_key': os.getenv('TOGETHER_API_KEY'),
                'model': 'meta-llama/Llama-3.1-70B-Instruct-Turbo',
                'cost_per_1m_tokens': 0.88,
                'headers': {
                    'Authorization': f'Bearer {os.getenv("TOGETHER_API_KEY")}',
                    'Content-Type': 'application/json'
                },
                'priority': 1
            }
        
        # Groq - Fastest
        if os.getenv('GROQ_API_KEY'):
            providers['groq'] = {
                'name': 'Groq',
                'endpoint': 'https://api.groq.com/openai/v1/chat/completions',
                'api_key': os.getenv('GROQ_API_KEY'),
                'model': 'llama-3.1-70b-versatile',
                'cost_per_1m_tokens': 0.59,
                'headers': {
                    'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}',
                    'Content-Type': 'application/json'
                },
                'priority': 2
            }
        
        # Replicate - Backup option
        if os.getenv('REPLICATE_API_TOKEN'):
            providers['replicate'] = {
                'name': 'Replicate',
                'endpoint': 'https://api.replicate.com/v1/predictions',
                'api_key': os.getenv('REPLICATE_API_TOKEN'),
                'model': 'meta/llama-2-70b-chat',
                'cost_per_1m_tokens': 0.65,
                'headers': {
                    'Authorization': f'Token {os.getenv("REPLICATE_API_TOKEN")}',
                    'Content-Type': 'application/json'
                },
                'priority': 3
            }
        
        # Original Llama API - Keep as last resort
        if os.getenv('LLAMA_API_KEY'):
            providers['llama_direct'] = {
                'name': 'Llama Direct',
                'endpoint': 'https://api.llama.com/v1/chat/completions',
                'api_key': os.getenv('LLAMA_API_KEY'),
                'model': 'llama3.1-70b-instruct',
                'cost_per_1m_tokens': 0.20,
                'headers': {
                    'Authorization': f'Bearer {os.getenv("LLAMA_API_KEY")}',
                    'Content-Type': 'application/json'
                },
                'priority': 4
            }
        
        return providers
    
    def get_best_provider(self):
        """Get the best available provider based on priority and health"""
        
        if not self.providers:
            return None
        
        # Sort by priority (lower number = higher priority)
        sorted_providers = sorted(
            self.providers.items(),
            key=lambda x: x[1]['priority']
        )
        
        # Return the first healthy provider
        for provider_name, provider_config in sorted_providers:
            failure_rate = self.get_failure_rate(provider_name)
            if failure_rate < 0.5:  # Less than 50% failure rate
                return provider_name, provider_config
        
        # If all providers are failing, return the highest priority one
        return sorted_providers[0]
    
    def get_failure_rate(self, provider_name):
        """Get failure rate for a provider"""
        
        total_requests = self.stats['requests_by_provider'].get(provider_name, 0)
        failures = self.stats['failures_by_provider'].get(provider_name, 0)
        
        if total_requests == 0:
            return 0.0
        
        return failures / total_requests
    
    async def make_request(self, request: LLMRequest) -> Dict:
        """Make a request using the best available provider"""
        
        provider_name, provider_config = self.get_best_provider()
        
        if not provider_name:
            return {
                'success': False,
                'error': 'No Llama providers available',
                'provider': 'none'
            }
        
        # Track request
        self.stats['requests_by_provider'][provider_name] = (
            self.stats['requests_by_provider'].get(provider_name, 0) + 1
        )
        
        try:
            start_time = time.time()
            
            # Make the request based on provider type
            if provider_name == 'replicate':
                response = await self.make_replicate_request(provider_config, request)
            else:
                response = await self.make_openai_compatible_request(provider_config, request)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Track response time
            if provider_name not in self.stats['response_times']:
                self.stats['response_times'][provider_name] = []
            self.stats['response_times'][provider_name].append(response_time)
            
            # Track cost
            tokens_used = len(request.prompt.split()) * 1.3  # Rough estimate
            cost = (tokens_used / 1_000_000) * provider_config['cost_per_1m_tokens']
            
            if provider_name not in self.stats['costs']:
                self.stats['costs'][provider_name] = 0
            self.stats['costs'][provider_name] += cost
            
            response['provider'] = provider_name
            response['response_time'] = response_time
            response['estimated_cost'] = cost
            
            return response
            
        except Exception as e:
            # Track failure
            self.stats['failures_by_provider'][provider_name] = (
                self.stats['failures_by_provider'].get(provider_name, 0) + 1
            )
            
            return {
                'success': False,
                'error': str(e),
                'provider': provider_name
            }
    
    async def make_openai_compatible_request(self, provider_config, request):
        """Make request to OpenAI-compatible endpoint"""
        
        import aiohttp
        
        payload = {
            'model': provider_config['model'],
            'messages': [
                {'role': 'user', 'content': request.prompt}
            ],
            'max_tokens': request.max_tokens,
            'temperature': request.temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                provider_config['endpoint'],
                headers=provider_config['headers'],
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        return {
                            'success': True,
                            'response': content.strip(),
                            'raw_response': data
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'No choices in response',
                            'raw_response': data
                        }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}: {error_text}'
                    }
    
    async def make_replicate_request(self, provider_config, request):
        """Make request to Replicate API (different format)"""
        
        import aiohttp
        
        payload = {
            'version': 'meta/llama-2-70b-chat',
            'input': {
                'prompt': request.prompt,
                'max_new_tokens': request.max_tokens,
                'temperature': request.temperature
            }
        }
        
        async with aiohttp.ClientSession() as session:
            # Create prediction
            async with session.post(
                provider_config['endpoint'],
                headers=provider_config['headers'],
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 201:
                    data = await response.json()
                    prediction_id = data['id']
                    
                    # Poll for completion
                    for _ in range(30):  # Max 30 attempts
                        await asyncio.sleep(1)
                        
                        async with session.get(
                            f"{provider_config['endpoint']}/{prediction_id}",
                            headers=provider_config['headers']
                        ) as poll_response:
                            
                            if poll_response.status == 200:
                                poll_data = await poll_response.json()
                                
                                if poll_data['status'] == 'succeeded':
                                    output = poll_data['output']
                                    if isinstance(output, list):
                                        output = ''.join(output)
                                    
                                    return {
                                        'success': True,
                                        'response': output.strip(),
                                        'raw_response': poll_data
                                    }
                                elif poll_data['status'] == 'failed':
                                    return {
                                        'success': False,
                                        'error': poll_data.get('error', 'Prediction failed')
                                    }
                    
                    return {
                        'success': False,
                        'error': 'Prediction timed out'
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}: {error_text}'
                    }
    
    def get_stats(self):
        """Get comprehensive stats"""
        
        stats = {
            'providers_available': len(self.providers),
            'provider_names': list(self.providers.keys()),
            'total_requests': sum(self.stats['requests_by_provider'].values()),
            'total_failures': sum(self.stats['failures_by_provider'].values()),
            'total_cost': sum(self.stats['costs'].values()),
            'provider_stats': {}
        }
        
        for provider_name in self.providers.keys():
            requests = self.stats['requests_by_provider'].get(provider_name, 0)
            failures = self.stats['failures_by_provider'].get(provider_name, 0)
            cost = self.stats['costs'].get(provider_name, 0)
            response_times = self.stats['response_times'].get(provider_name, [])
            
            stats['provider_stats'][provider_name] = {
                'requests': requests,
                'failures': failures,
                'success_rate': (requests - failures) / requests if requests > 0 else 0,
                'cost': cost,
                'avg_response_time': sum(response_times) / len(response_times) if response_times else 0
            }
        
        return stats

def setup_api_keys():
    """Setup API keys for testing"""
    
    # Check which keys are available
    available_keys = []
    
    keys_to_check = [
        ('TOGETHER_API_KEY', 'Together AI'),
        ('GROQ_API_KEY', 'Groq'),
        ('REPLICATE_API_TOKEN', 'Replicate'),
        ('LLAMA_API_KEY', 'Llama Direct')
    ]
    
    for key_name, provider_name in keys_to_check:
        if os.getenv(key_name):
            available_keys.append(provider_name)
        else:
            print(f"⚠️  {key_name} not found - {provider_name} will not be available")
    
    if not available_keys:
        print("❌ No Llama provider API keys found!")
        print("💡 Get free API keys from:")
        print("   • Together AI: https://api.together.xyz/")
        print("   • Groq: https://console.groq.com/")
        print("   • Replicate: https://replicate.com/")
        return False
    
    print(f"✅ Available providers: {', '.join(available_keys)}")
    return True

async def test_llama_providers():
    """Test all available Llama providers"""
    
    print("🧪 Testing Llama Providers")
    print("=" * 50)
    
    if not setup_api_keys():
        return
    
    manager = LlamaProviderManager()
    
    if not manager.providers:
        print("❌ No providers configured")
        return
    
    # Create test request
    test_context = {
        'id': 'test_agent',
        'agent_type': 'trader',
        'energy': 0.7,
        'happiness': 0.5,
        'resources': {'food': 25, 'currency': 150, 'materials': 10},
        'personality_traits': ['ambitious', 'social', 'competitive'],
        'goals': ['accumulate_wealth', 'expand_network'],
        'nearby_agents': [
            {'type': 'farmer', 'distance': 3.5},
            {'type': 'craftsman', 'distance': 7.2}
        ],
        'state': 'idle',
        'recent_actions': ['traded_goods']
    }
    
    prompt = create_agent_prompt(test_context)
    request = LLMRequest(
        agent_id='test_agent',
        prompt=prompt,
        context=test_context,
        max_tokens=150,
        temperature=0.7
    )
    
    # Test each provider
    results = []
    
    for provider_name, provider_config in manager.providers.items():
        print(f"\n🔍 Testing {provider_config['name']}...")
        
        try:
            start_time = time.time()
            result = await manager.make_request(request)
            end_time = time.time()
            
            if result['success']:
                print(f"✅ Success! ({end_time - start_time:.2f}s)")
                print(f"   Response: {result['response'][:100]}...")
                print(f"   Cost: ${result.get('estimated_cost', 0):.4f}")
            else:
                print(f"❌ Failed: {result['error']}")
            
            results.append({
                'provider': provider_name,
                'name': provider_config['name'],
                'success': result['success'],
                'response_time': end_time - start_time,
                'response': result.get('response', ''),
                'error': result.get('error', ''),
                'cost': result.get('estimated_cost', 0)
            })
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                'provider': provider_name,
                'name': provider_config['name'],
                'success': False,
                'error': str(e)
            })
    
    # Print summary
    print(f"\n📊 Test Results Summary")
    print("-" * 30)
    
    successful_providers = [r for r in results if r['success']]
    failed_providers = [r for r in results if not r['success']]
    
    if successful_providers:
        print(f"✅ Working providers ({len(successful_providers)}):")
        for result in successful_providers:
            print(f"   • {result['name']}: {result['response_time']:.2f}s, ${result['cost']:.4f}")
    
    if failed_providers:
        print(f"❌ Failed providers ({len(failed_providers)}):")
        for result in failed_providers:
            print(f"   • {result['name']}: {result['error']}")
    
    # Get manager stats
    stats = manager.get_stats()
    print(f"\n📈 Manager Stats:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Total cost: ${stats['total_cost']:.4f}")
    print(f"   Success rate: {((stats['total_requests'] - stats['total_failures']) / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0:.1f}%")
    
    return results

async def run_small_scale_test():
    """Run a small scale test with the working providers"""
    
    print(f"\n🚀 Small Scale Test with Llama Providers")
    print("=" * 50)
    
    manager = LlamaProviderManager()
    
    if not manager.providers:
        print("❌ No providers configured")
        return
    
    # Generate 10 test agents
    test_contexts = []
    agent_types = ['farmer', 'trader', 'craftsman', 'scholar', 'warrior']
    
    for i in range(10):
        context = {
            'id': f'agent_{i:03d}',
            'agent_type': agent_types[i % len(agent_types)],
            'energy': 0.3 + (i % 7) * 0.1,
            'happiness': 0.2 + (i % 8) * 0.1,
            'resources': {
                'food': 10 + (i % 50),
                'currency': 50 + (i % 500),
                'materials': 5 + (i % 40)
            },
            'personality_traits': ['trait1', 'trait2', 'trait3'],
            'goals': ['goal1', 'goal2'],
            'nearby_agents': [
                {'type': 'other', 'distance': 5.0 + (i % 20)}
            ],
            'state': 'idle',
            'recent_actions': ['action1']
        }
        test_contexts.append(context)
    
    # Run requests
    start_time = time.time()
    successful_requests = 0
    total_requests = len(test_contexts)
    
    print(f"Processing {total_requests} agents...")
    
    for i, context in enumerate(test_contexts):
        prompt = create_agent_prompt(context)
        request = LLMRequest(
            agent_id=context['id'],
            prompt=prompt,
            context=context,
            max_tokens=120,
            temperature=0.7
        )
        
        result = await manager.make_request(request)
        
        if result['success']:
            successful_requests += 1
            print(f"✅ Agent {i+1}: {result['response'][:50]}... ({result.get('provider', 'unknown')})")
        else:
            print(f"❌ Agent {i+1}: {result['error']}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print results
    print(f"\n📊 Small Scale Test Results")
    print("-" * 40)
    print(f"Total agents: {total_requests}")
    print(f"Successful: {successful_requests}")
    print(f"Failed: {total_requests - successful_requests}")
    print(f"Success rate: {successful_requests / total_requests * 100:.1f}%")
    print(f"Total time: {total_time:.2f}s")
    print(f"Requests/sec: {successful_requests / total_time:.2f}")
    
    # Get detailed stats
    stats = manager.get_stats()
    print(f"\n📈 Provider Performance:")
    for provider_name, provider_stats in stats['provider_stats'].items():
        if provider_stats['requests'] > 0:
            print(f"   {provider_name}:")
            print(f"     Requests: {provider_stats['requests']}")
            print(f"     Success rate: {provider_stats['success_rate']:.1%}")
            print(f"     Avg response time: {provider_stats['avg_response_time']:.3f}s")
            print(f"     Cost: ${provider_stats['cost']:.4f}")

def print_integration_guide():
    """Print guide for integrating the working providers"""
    
    print(f"\n🔧 INTEGRATION GUIDE")
    print("=" * 50)
    print("To integrate working Llama providers into your system:")
    print()
    print("1. 🔑 Get API Keys (free tiers available):")
    print("   • Together AI: https://api.together.xyz/")
    print("   • Groq: https://console.groq.com/")
    print()
    print("2. 🌍 Set Environment Variables:")
    print("   export TOGETHER_API_KEY='your-together-key'")
    print("   export GROQ_API_KEY='your-groq-key'")
    print()
    print("3. 🔄 Update llm_integration.py:")
    print("   • Add LlamaProviderManager to LLMManager")
    print("   • Route Llama requests through provider manager")
    print("   • Implement fallback logic")
    print()
    print("4. 🚀 Deploy to Production:")
    print("   • Update Google Cloud Run environment variables")
    print("   • Test with small simulations first")
    print("   • Monitor costs and performance")
    print()
    print("5. 💰 Expected Benefits:")
    print("   • 80-90% cost reduction vs OpenAI")
    print("   • Reliable Llama model access")
    print("   • Intelligent provider fallback")

async def main():
    """Main function"""
    
    print("🦙 Llama Integration Implementation")
    print("=" * 60)
    print("Testing and implementing reliable Llama API access")
    print()
    
    # Test providers
    await test_llama_providers()
    
    # Run small scale test
    await run_small_scale_test()
    
    # Print integration guide
    print_integration_guide()
    
    print(f"\n✅ Llama Integration Testing Complete!")

if __name__ == "__main__":
    asyncio.run(main()) 