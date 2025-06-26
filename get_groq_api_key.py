#!/usr/bin/env python3
"""
Get Groq API Key - Interactive Setup Guide
Helps you get a free Groq API key for Llama 3.1 70B access
"""

import os
import sys
import webbrowser
from getpass import getpass

def print_header():
    """Print header"""
    print("🦙 GROQ API KEY SETUP")
    print("=" * 50)
    print("Get FREE access to Llama 3.1 70B (faster than GPT-4)")
    print()

def open_groq_signup():
    """Open Groq signup page"""
    print("📋 Step 1: Sign up for free Groq account")
    print("-" * 40)
    print("I'll open the Groq signup page in your browser...")
    print("URL: https://console.groq.com/")
    print()
    
    try:
        webbrowser.open('https://console.groq.com/')
        print("✅ Browser opened!")
    except:
        print("❌ Couldn't open browser automatically")
        print("💡 Please manually go to: https://console.groq.com/")
    
    print()
    print("📝 On the Groq website:")
    print("  1. Click 'Sign Up' (no credit card required)")
    print("  2. Enter your email and create password")
    print("  3. Verify your email address")
    print("  4. Log in to the console")
    print()
    
    input("Press Enter when you've signed up and logged in...")

def get_api_key_instructions():
    """Guide user through getting API key"""
    print("\n🔑 Step 2: Get your API key")
    print("-" * 40)
    print("In the Groq console:")
    print("  1. Look for 'API Keys' in the left sidebar")
    print("  2. Click 'Create API Key'")
    print("  3. Give it a name (e.g., 'NOUS-Simulation')")
    print("  4. Click 'Create'")
    print("  5. Copy the generated key (starts with 'gsk_')")
    print()
    print("⚠️  Important: Copy the key now - you won't see it again!")
    print()

def collect_api_key():
    """Collect API key from user"""
    print("🔐 Step 3: Enter your API key")
    print("-" * 40)
    
    while True:
        api_key = getpass("Paste your Groq API key (hidden input): ").strip()
        
        if not api_key:
            print("❌ No API key entered. Please try again.")
            continue
        
        if not api_key.startswith('gsk_'):
            print("⚠️  Groq API keys usually start with 'gsk_'")
            confirm = input("Continue anyway? (y/n): ").lower()
            if confirm != 'y':
                continue
        
        # Confirm the key
        print(f"✅ API key entered: {api_key[:10]}...{api_key[-4:]}")
        confirm = input("Is this correct? (y/n): ").lower()
        
        if confirm == 'y':
            return api_key
        
        print("Let's try again...")

def save_api_key(api_key):
    """Save API key to environment"""
    print("\n💾 Step 4: Save API key")
    print("-" * 40)
    
    # Set for current session
    os.environ['GROQ_API_KEY'] = api_key
    print("✅ API key set for current session")
    
    # Provide instructions for permanent setup
    print("\n🔧 To make this permanent, add to your shell profile:")
    print(f"   echo 'export GROQ_API_KEY=\"{api_key}\"' >> ~/.zshrc")
    print("   source ~/.zshrc")
    print()
    print("Or for bash:")
    print(f"   echo 'export GROQ_API_KEY=\"{api_key}\"' >> ~/.bashrc")
    print("   source ~/.bashrc")
    print()
    
    # Save to .env file for convenience
    try:
        with open('.env', 'a') as f:
            f.write(f"\n# Groq API Key\nGROQ_API_KEY={api_key}\n")
        print("✅ Also saved to .env file in current directory")
    except:
        print("⚠️  Couldn't save to .env file (not critical)")

async def test_api_key():
    """Test the API key"""
    print("\n🧪 Step 5: Test your API key")
    print("-" * 40)
    
    try:
        import aiohttp
        import json
        
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            print("❌ API key not found in environment")
            return False
        
        print("🔍 Testing API key...")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'llama-3.1-8b-instant',
            'messages': [
                {'role': 'user', 'content': 'Say hello and confirm you are Llama 3.1 running on Groq'}
            ],
            'max_tokens': 50,
            'temperature': 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        print("✅ API key works!")
                        print(f"🤖 Llama response: {content}")
                        
                        # Show usage info
                        if 'usage' in data:
                            usage = data['usage']
                            print(f"📊 Tokens used: {usage.get('total_tokens', 'N/A')}")
                        
                        return True
                    else:
                        print("❌ Unexpected response format")
                        print(f"Response: {data}")
                        return False
                
                elif response.status == 401:
                    print("❌ API key is invalid")
                    print("💡 Please check your API key and try again")
                    return False
                
                elif response.status == 429:
                    print("⚠️  Rate limit exceeded")
                    print("💡 This is normal - your API key works!")
                    return True
                
                else:
                    error_text = await response.text()
                    print(f"❌ API test failed: HTTP {response.status}")
                    print(f"Error: {error_text}")
                    return False
                    
    except ImportError:
        print("⚠️  aiohttp not installed - skipping API test")
        print("💡 Install with: pip install aiohttp")
        return True
    
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def print_next_steps():
    """Print next steps"""
    print("\n🚀 NEXT STEPS")
    print("=" * 50)
    print("Your Groq API key is ready! Here's what you can do:")
    print()
    print("1. 🧪 Test Groq Llama integration:")
    print("   python groq_llama_implementation.py")
    print()
    print("2. 🔄 Update the main LLM integration:")
    print("   python update_llm_integration.py")
    print()
    print("3. 🚀 Deploy to production:")
    print("   python deploy_real_llm_production.py")
    print()
    print("💡 Benefits you'll get:")
    print("   • FREE Llama 3.1 70B access")
    print("   • 284 tokens/second (faster than GPT-4)")
    print("   • 90% cost reduction vs OpenAI")
    print("   • No billing required")
    print()
    print("📊 Free tier limits:")
    print("   • 6,000 tokens per minute")
    print("   • Perfect for testing and small simulations")
    print("   • Upgrade available for higher limits")

async def main():
    """Main function"""
    
    print_header()
    
    # Check if already configured
    if os.getenv('GROQ_API_KEY'):
        print("✅ GROQ_API_KEY already configured!")
        print(f"   Key: {os.getenv('GROQ_API_KEY')[:10]}...")
        print()
        
        test_existing = input("Test existing API key? (y/n): ").lower()
        if test_existing == 'y':
            success = await test_api_key()
            if success:
                print_next_steps()
                return
            else:
                print("❌ Existing key doesn't work. Let's get a new one...")
                print()
    
    # Guide through setup
    open_groq_signup()
    get_api_key_instructions()
    api_key = collect_api_key()
    save_api_key(api_key)
    
    # Test the key
    success = await test_api_key()
    
    if success:
        print_next_steps()
    else:
        print("\n❌ Setup incomplete")
        print("💡 Please check your API key and try again")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 