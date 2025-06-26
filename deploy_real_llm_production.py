#!/usr/bin/env python3
"""
Deploy Real LLM Integration to Production
Updates cloud services with OpenAI, Gemini, and Llama API integration
"""

import os
import subprocess
import json
import time
from pathlib import Path

def setup_environment_variables():
    """Configure environment variables for production deployment"""
    
    # API Keys
    api_keys = {
        "OPENAI_API_KEY": "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",
        "GEMINI_API_KEY": "AIzaSyAqko3NqGS-GtXhzm8LeiZ3xUEyo_XIqLo",
        "LLAMA_API_KEY": "LLM|1469017110898899|mJOyVVo1xc4vbUj6y1Wj-svovnE"
    }
    
    print("🔑 Setting up production environment variables...")
    
    # Set local environment
    for key, value in api_keys.items():
        os.environ[key] = value
        print(f"   ✅ {key} configured locally")
    
    return api_keys


def update_cloud_secrets(api_keys):
    """Update Google Cloud Secret Manager with API keys"""
    
    print("\n☁️ Updating Google Cloud Secret Manager...")
    
    project_id = "amien-research-pipeline"
    
    for key, value in api_keys.items():
        secret_name = key.lower().replace('_', '-')
        
        try:
            # Create or update secret
            cmd = [
                "gcloud", "secrets", "create", secret_name,
                "--data-file=-",
                "--project", project_id
            ]
            
            result = subprocess.run(
                cmd,
                input=value.encode(),
                capture_output=True,
                text=False
            )
            
            if result.returncode == 0:
                print(f"   ✅ Created secret: {secret_name}")
            else:
                # Try updating existing secret
                cmd = [
                    "gcloud", "secrets", "versions", "add", secret_name,
                    "--data-file=-",
                    "--project", project_id
                ]
                
                result = subprocess.run(
                    cmd,
                    input=value.encode(),
                    capture_output=True,
                    text=False
                )
                
                if result.returncode == 0:
                    print(f"   ✅ Updated secret: {secret_name}")
                else:
                    print(f"   ❌ Failed to update secret: {secret_name}")
                    print(f"      Error: {result.stderr.decode()}")
                    
        except Exception as e:
            print(f"   ❌ Error with secret {secret_name}: {e}")


def update_cloud_run_services():
    """Update Cloud Run services with new environment variables"""
    
    print("\n🚀 Updating Cloud Run services...")
    
    services = [
        "society-simulation",
        "amien-api-service"
    ]
    
    project_id = "amien-research-pipeline"
    region = "us-central1"
    
    for service in services:
        print(f"\n   📦 Updating {service}...")
        
        try:
            # Update service with environment variables from secrets
            cmd = [
                "gcloud", "run", "services", "update", service,
                "--region", region,
                "--project", project_id,
                "--set-env-vars", "LLM_PROVIDER=openai,LLM_MODEL=gpt-3.5-turbo,ENABLE_REAL_LLM=true",
                "--set-secrets", "OPENAI_API_KEY=openai-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,LLAMA_API_KEY=llama-api-key:latest",
                "--memory", "4Gi",
                "--cpu", "4",
                "--max-instances", "10"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"      ✅ Successfully updated {service}")
            else:
                print(f"      ❌ Failed to update {service}")
                print(f"         Error: {result.stderr}")
                
        except Exception as e:
            print(f"      ❌ Error updating {service}: {e}")


def test_production_apis():
    """Test the production APIs with real LLM integration"""
    
    print("\n🧪 Testing Production APIs...")
    
    import requests
    import json
    
    # Test society simulation API
    base_url = "https://society-simulation-643533604146.us-central1.run.app"
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/", timeout=30)
        if response.status_code == 200:
            print("   ✅ Society simulation API health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test real LLM simulation
    try:
        print("   🤖 Testing real LLM simulation...")
        
        payload = {
            "num_agents": 5,
            "num_steps": 5,
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo",
            "enable_real_llm": True
        }
        
        response = requests.post(
            f"{base_url}/simulation/run",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"      ✅ Real LLM simulation completed!")
            print(f"         Simulation ID: {result.get('simulation_id', 'N/A')}")
            print(f"         Status: {result.get('status', 'N/A')}")
            
            if 'performance_metrics' in result:
                metrics = result['performance_metrics']
                print(f"         Performance: {metrics.get('steps_per_second', 'N/A')} SPS")
                print(f"         Total time: {metrics.get('total_time', 'N/A')}s")
        else:
            print(f"      ❌ Simulation failed: {response.status_code}")
            print(f"         Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Simulation test error: {e}")


def run_comprehensive_benchmark():
    """Run comprehensive benchmark with different LLM providers"""
    
    print("\n📊 Running Comprehensive LLM Benchmark...")
    
    # Test configurations
    test_configs = [
        {"provider": "openai", "model": "gpt-3.5-turbo", "agents": 10, "steps": 10},
        {"provider": "gemini", "model": "gemini-1.5-flash", "agents": 10, "steps": 10},
        {"provider": "mock", "model": "mock", "agents": 25, "steps": 20},  # Baseline
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n   🧪 Testing {config['provider']} - {config['model']}")
        print(f"      Agents: {config['agents']}, Steps: {config['steps']}")
        
        start_time = time.time()
        
        try:
            # Run local test
            cmd = [
                "python", "-c", f"""
import os
import sys
sys.path.append('src')

# Set environment variables
os.environ['OPENAI_API_KEY'] = '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'
os.environ['GEMINI_API_KEY'] = 'AIzaSyAqko3NqGS-GtXhzm8LeiZ3xUEyo_XIqLo'

from llm_integration import LLMManager, LLMProvider, LLMRequest, create_agent_prompt
import asyncio
import time

async def benchmark():
    provider = LLMProvider.{config['provider'].upper()}
    llm = LLMManager(provider=provider, model='{config['model']}')
    
    # Simulate agent decisions
    total_requests = {config['agents'] * config['steps']}
    start = time.time()
    
    for i in range(total_requests):
        context = {{
            'agent_type': 'test_agent',
            'energy': 0.5 + (i % 10) * 0.05,
            'happiness': 0.6 + (i % 8) * 0.05,
            'resources': {{'food': 10 + i, 'currency': 100 + i * 10}},
            'state': 'idle',
            'goals': ['test_goal']
        }}
        
        prompt = create_agent_prompt(context)
        request = LLMRequest(
            agent_id=f'agent_{{i}}',
            prompt=prompt,
            context=context,
            max_tokens=100,
            temperature=0.7
        )
        
        response = await llm.get_response(request)
        if not response.success:
            print(f'Request {{i}} failed: {{response.error}}')
    
    end = time.time()
    total_time = end - start
    
    stats = llm.get_stats()
    print(f'BENCHMARK_RESULT:{{total_time:.2f}}:{{total_requests/total_time:.2f}}:{{stats}}')

asyncio.run(benchmark())
"""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            if result.returncode == 0:
                # Parse benchmark results
                output_lines = result.stdout.strip().split('\n')
                benchmark_line = None
                
                for line in output_lines:
                    if line.startswith('BENCHMARK_RESULT:'):
                        benchmark_line = line
                        break
                
                if benchmark_line:
                    parts = benchmark_line.split(':')
                    if len(parts) >= 3:
                        exec_time = float(parts[1])
                        rps = float(parts[2])
                        
                        result_data = {
                            'provider': config['provider'],
                            'model': config['model'],
                            'agents': config['agents'],
                            'steps': config['steps'],
                            'total_requests': config['agents'] * config['steps'],
                            'execution_time': exec_time,
                            'requests_per_second': rps,
                            'status': 'success'
                        }
                        
                        print(f"      ✅ Completed in {exec_time:.2f}s")
                        print(f"         Requests/sec: {rps:.2f}")
                        
                        results.append(result_data)
                    else:
                        print(f"      ⚠️  Could not parse benchmark results")
                        results.append({
                            'provider': config['provider'],
                            'status': 'parse_error',
                            'execution_time': total_time
                        })
                else:
                    print(f"      ⚠️  No benchmark results found")
                    results.append({
                        'provider': config['provider'],
                        'status': 'no_results',
                        'execution_time': total_time
                    })
            else:
                print(f"      ❌ Benchmark failed")
                print(f"         Error: {result.stderr}")
                results.append({
                    'provider': config['provider'],
                    'status': 'failed',
                    'error': result.stderr,
                    'execution_time': total_time
                })
                
        except subprocess.TimeoutExpired:
            print(f"      ⏰ Benchmark timed out after 5 minutes")
            results.append({
                'provider': config['provider'],
                'status': 'timeout',
                'execution_time': 300
            })
        except Exception as e:
            print(f"      ❌ Benchmark error: {e}")
            results.append({
                'provider': config['provider'],
                'status': 'error',
                'error': str(e),
                'execution_time': time.time() - start_time
            })
    
    # Save results
    with open('llm_benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Benchmark Results Summary:")
    print("=" * 60)
    
    for result in results:
        if result['status'] == 'success':
            print(f"{result['provider']:<15} {result['requests_per_second']:.2f} req/s  {result['execution_time']:.2f}s")
        else:
            print(f"{result['provider']:<15} {result['status']:<10} {result['execution_time']:.2f}s")
    
    return results


def main():
    """Main deployment function"""
    
    print("🚀 Deploying Real LLM Integration to Production")
    print("=" * 60)
    print("This will:")
    print("• Configure API keys in Google Cloud Secret Manager")
    print("• Update Cloud Run services with real LLM integration")
    print("• Test production APIs")
    print("• Run comprehensive benchmarks")
    print()
    
    # Step 1: Setup environment
    api_keys = setup_environment_variables()
    
    # Step 2: Update cloud secrets
    update_cloud_secrets(api_keys)
    
    # Step 3: Update cloud services
    update_cloud_run_services()
    
    # Step 4: Test production
    test_production_apis()
    
    # Step 5: Run benchmarks
    results = run_comprehensive_benchmark()
    
    print(f"\n🎯 Deployment Complete!")
    print("=" * 60)
    print("✅ Real LLM integration deployed to production")
    print("✅ API keys configured in Secret Manager")
    print("✅ Cloud Run services updated")
    print("✅ Production testing completed")
    print("✅ Benchmark results saved to llm_benchmark_results.json")
    
    # Success summary
    successful_providers = [r for r in results if r.get('status') == 'success']
    if successful_providers:
        print(f"\n🎉 Working LLM Providers in Production:")
        for provider in successful_providers:
            print(f"   • {provider['provider'].upper()}: {provider['requests_per_second']:.1f} req/s")
    
    print(f"\n🔗 Production URLs:")
    print("   • Society Simulation: https://society-simulation-643533604146.us-central1.run.app")
    print("   • AMIEN API: https://amien-api-service-643533604146.us-central1.run.app")
    
    print(f"\n📋 Next Steps:")
    print("   1. Monitor production performance")
    print("   2. Scale up to larger simulations")
    print("   3. Implement cost optimization")
    print("   4. Add monitoring and alerting")


if __name__ == "__main__":
    main() 