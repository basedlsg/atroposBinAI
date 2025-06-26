#!/usr/bin/env python3
"""
Simple Groq API test using only standard library modules
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl

def test_groq_api():
    """Test Groq API with a simple spatial reasoning prompt"""
    
    # Get API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    print(f"✅ Using Groq API key: {api_key[:20]}...")
    
    # Test prompt
    prompt = """You are an AI agent in a 3D environment. You need to navigate from position (0,0,0) to target (10,10,10).

Current environment state:
- Your position: (0, 0, 0)
- Target position: (10, 10, 10)
- Obstacles: [(5, 5, 5), (8, 8, 8)]
- Available actions: MOVE_FORWARD, MOVE_LEFT, MOVE_RIGHT, MOVE_UP, MOVE_DOWN

Based on this information, what is the best next action to take? Respond with only the action name."""

    # Prepare request
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Create request
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        # Create SSL context that ignores certificate verification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        print("🔄 Sending request to Groq API...")
        
        # Make request
        with urllib.request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ API Response: {content}")
                return True
            else:
                print(f"❌ Unexpected response format: {result}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print(f"Response: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Groq API Integration")
    print("=" * 40)
    
    success = test_groq_api()
    
    if success:
        print("\n✅ Groq API test successful!")
        print("The API is working and can be used for spatial reasoning tasks.")
    else:
        print("\n❌ Groq API test failed!")
        print("Please check your API key and network connection.") 