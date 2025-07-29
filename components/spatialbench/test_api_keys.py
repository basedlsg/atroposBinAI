#!/usr/bin/env python3
"""
Test API connectivity with provided keys
"""
import os
import asyncio
import sys
from pathlib import Path

# Set API keys as environment variables
# To run this test, set the following environment variables:
# export GEMINI_API_KEY="your_gemini_api_key"
# export LLAMA_API_KEY="your_llama_api_key"
# export GROQ_API_KEY="your_groq_api_key"

async def test_gemini_api():
    """Test Gemini API connectivity"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        model = genai.GenerativeModel('gemini-pro')
        
        response = await asyncio.to_thread(
            model.generate_content,
            "Test: What is 2+2? Answer with just the number."
        )
        
        print(f"✅ Gemini API: Working (Response: {response.text.strip()})")
        return True
        
    except ImportError:
        print("⚠️ Gemini API: google-generativeai not installed")
        return False
    except Exception as e:
        print(f"❌ Gemini API: Error - {e}")
        return False

async def test_groq_api():
    """Test Groq API connectivity"""
    try:
        import groq
        
        client = groq.Groq(api_key=os.environ['GROQ_API_KEY'])
        
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "user", "content": "Test: What is 2+2? Answer with just the number."}
            ],
            max_tokens=10,
            temperature=0.0
        )
        
        print(f"✅ Groq API: Working (Response: {response.choices[0].message.content.strip()})")
        return True
        
    except ImportError:
        print("⚠️ Groq API: groq not installed")
        return False
    except Exception as e:
        print(f"❌ Groq API: Error - {e}")
        return False

async def test_llama_api():
    """Test LLAMA API connectivity"""
    try:
        import httpx
        
        headers = {
            "Authorization": f"Bearer {os.environ['LLAMA_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.2-90b-vision",
            "messages": [
                {"role": "user", "content": "Test: What is 2+2? Answer with just the number."}
            ],
            "max_tokens": 10,
            "temperature": 0.0
        }
        
        # Note: This is a placeholder URL - would need actual LLAMA API endpoint
        print("⚠️ LLAMA API: Need actual API endpoint URL to test")
        return None
        
    except ImportError:
        print("⚠️ LLAMA API: httpx not installed")
        return False
    except Exception as e:
        print(f"❌ LLAMA API: Error - {e}")
        return False

async def test_spatial_reasoning_task():
    """Test a simple spatial reasoning task with Gemini"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        model = genai.GenerativeModel('gemini-pro')
        
        spatial_prompt = """
        You are at position (0,0) on a grid. You move 2 steps north, then 3 steps east, then 1 step south.
        What is your final position? Answer in the format (x,y).
        """
        
        response = await asyncio.to_thread(
            model.generate_content,
            spatial_prompt
        )
        
        print(f"🧠 Spatial reasoning test: {response.text.strip()}")
        
        # Check if response contains (3,1) which is the correct answer
        expected = "(3,1)"
        if expected in response.text:
            print(f"✅ Spatial reasoning: Correct answer found!")
            return True
        else:
            print(f"⚠️ Spatial reasoning: Answer may be incorrect")
            return False
        
    except Exception as e:
        print(f"❌ Spatial reasoning test failed: {e}")
        return False

async def main():
    """Test all API connections"""
    print("🔑 Testing API Keys and Spatial Reasoning")
    print("=" * 50)
    
    # Test APIs
    results = {}
    
    print("\n📡 Testing API Connectivity:")
    results['gemini'] = await test_gemini_api()
    results['groq'] = await test_groq_api()
    results['llama'] = await test_llama_api()
    
    print("\n🧠 Testing Spatial Reasoning:")
    results['spatial'] = await test_spatial_reasoning_task()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 API Test Summary:")
    print("=" * 50)
    
    working_apis = [k for k, v in results.items() if v is True]
    print(f"✅ Working APIs: {working_apis}")
    
    if results.get('gemini'):
        print("\n🚀 Ready to run simplified multimodal experiment!")
        print("   • Gemini Pro available for text-only tasks")
        print("   • Can test spatial reasoning capabilities")
        
        if results.get('groq'):
            print("   • Groq available for speed comparison")
        
        print("\n📝 Recommended next steps:")
        print("   1. Run simplified experiment with working APIs")
        print("   2. Fix LLAMA API endpoint for full multimodal test")
        print("   3. Deploy to Google Cloud for scale")
        
        return True
    else:
        print("\n❌ Cannot proceed - need at least Gemini API working")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)