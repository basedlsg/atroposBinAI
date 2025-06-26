#!/usr/bin/env python3
"""
Setup script for real LLM API integration
Configures API keys and tests all LLM providers
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm_integration import LLMManager, LLMProvider, LLMRequest, create_agent_prompt


def setup_environment_variables():
    """Set up environment variables for all LLM providers"""
    
    # API Keys provided
    api_keys = {
        "OPENAI_API_KEY": "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",
        "GEMINI_API_KEY": "AIzaSyAqko3NqGS-GtXhzm8LeiZ3xUEyo_XIqLo",
        "LLAMA_API_KEY": "LLM|1469017110898899|mJOyVVo1xc4vbUj6y1Wj-svovnE"
    }
    
    print("🔑 Setting up API keys...")
    for key, value in api_keys.items():
        os.environ[key] = value
        print(f"   ✅ {key} configured")
    
    print("\n💡 To make these permanent, add to your shell profile:")
    for key, value in api_keys.items():
        print(f"export {key}=\"{value}\"")


async def test_llm_provider(provider: LLMProvider, model: str = None):
    """Test a specific LLM provider"""
    print(f"\n🧪 Testing {provider.value.upper()}")
    print("=" * 50)
    
    try:
        # Initialize LLM manager
        llm = LLMManager(provider=provider, model=model)
        
        if llm.provider == LLMProvider.NONE:
            print(f"❌ {provider.value} initialization failed - falling back to rule-based")
            return False
        
        # Create test context
        test_context = {
            "agent_type": "farmer",
            "energy": 0.4,
            "happiness": 0.7,
            "resources": {"food": 30, "currency": 150, "materials": 8},
            "nearby_agents": [
                {"type": "trader", "distance": 12.5},
                {"type": "craftsman", "distance": 18.0}
            ],
            "state": "idle",
            "goals": ["accumulate_wealth", "make_friends"]
        }
        
        # Generate prompt
        prompt = create_agent_prompt(test_context)
        request = LLMRequest(
            agent_id="test_farmer_001",
            prompt=prompt,
            context=test_context,
            max_tokens=200,
            temperature=0.7
        )
        
        print(f"📝 Prompt (first 200 chars):")
        print(f"   {prompt[:200]}...")
        
        # Get response
        print(f"\n⏳ Calling {provider.value} API...")
        response = await llm.get_response(request)
        
        if response.success:
            print(f"✅ SUCCESS!")
            print(f"   Provider: {response.provider}")
            print(f"   Latency: {response.latency:.3f}s")
            print(f"   Response: {response.response}")
            
            # Get stats
            stats = llm.get_stats()
            print(f"\n📊 Stats:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
            
            return True
        else:
            print(f"❌ FAILED: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_all_providers():
    """Test all available LLM providers"""
    print("🚀 Testing All LLM Providers")
    print("=" * 60)
    
    # Test configurations
    test_configs = [
        (LLMProvider.OPENAI, "gpt-3.5-turbo"),
        (LLMProvider.GEMINI, "gemini-1.5-flash"),
        (LLMProvider.LLAMA, "llama3.1-70b-instruct"),
        (LLMProvider.MOCK, None),
    ]
    
    results = {}
    
    for provider, model in test_configs:
        success = await test_llm_provider(provider, model)
        results[provider.value] = success
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n🎯 SUMMARY")
    print("=" * 60)
    
    working_providers = []
    failed_providers = []
    
    for provider, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"   {provider.upper():<15} {status}")
        
        if success:
            working_providers.append(provider)
        else:
            failed_providers.append(provider)
    
    print(f"\n📈 Results:")
    print(f"   Working providers: {len(working_providers)}")
    print(f"   Failed providers: {len(failed_providers)}")
    
    if working_providers:
        print(f"\n🎉 Ready for production with: {', '.join(working_providers)}")
    
    return results


async def run_society_simulation_test():
    """Run a small society simulation with real LLM"""
    print(f"\n🏘️ Running Society Simulation Test with Real LLM")
    print("=" * 60)
    
    # Import simulation components
    try:
        from run_simulation import main as run_sim
        
        print("🧪 Testing 10 agents, 20 steps with OpenAI...")
        
        # Set command line args programmatically
        import sys
        original_argv = sys.argv.copy()
        
        sys.argv = [
            "run_simulation.py",
            "--agents", "10",
            "--steps", "20", 
            "--llm", "openai",
            "--model", "gpt-3.5-turbo"
        ]
        
        try:
            await run_sim()
            print("✅ Society simulation test completed successfully!")
        finally:
            sys.argv = original_argv
            
    except Exception as e:
        print(f"❌ Society simulation test failed: {e}")
        print("   This is expected if run_simulation.py needs updates")


def install_dependencies():
    """Install required dependencies"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        "openai",
        "google-generativeai", 
        "requests",
        "asyncio"
    ]
    
    import subprocess
    import importlib
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "google-generativeai":
                importlib.import_module("google.generativeai")
            else:
                importlib.import_module(package)
            print(f"   ✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} missing")
    
    if missing_packages:
        print(f"\n📥 Installing missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"   ✅ Installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install {package}: {e}")
    else:
        print("   🎉 All dependencies satisfied!")


async def main():
    """Main setup and test function"""
    print("🌟 LLM API Integration Setup & Test")
    print("=" * 60)
    print("Setting up real LLM API integration for society simulation")
    print("This will test OpenAI, Gemini, and Llama APIs")
    
    # Step 1: Install dependencies
    install_dependencies()
    
    # Step 2: Setup environment variables
    setup_environment_variables()
    
    # Step 3: Test all providers
    results = await test_all_providers()
    
    # Step 4: Run simulation test if any provider works
    working_providers = [p for p, success in results.items() if success and p != "mock"]
    if working_providers:
        await run_society_simulation_test()
    
    print(f"\n🎯 Setup Complete!")
    print("=" * 60)
    
    if working_providers:
        print("✅ Ready to run society simulations with real LLM!")
        print("\nNext steps:")
        print("1. Run simulation with OpenAI:")
        print("   python run_simulation.py --agents 25 --llm openai --steps 100")
        print("\n2. Run simulation with Gemini:")
        print("   python run_simulation.py --agents 25 --llm gemini --steps 100")
        print("\n3. Run simulation with Llama:")
        print("   python run_simulation.py --agents 25 --llm llama --steps 100")
        print("\n4. Compare performance:")
        print("   python run_simulation.py --benchmark --llm openai")
    else:
        print("❌ No LLM providers working. Check API keys and network connection.")


if __name__ == "__main__":
    asyncio.run(main()) 