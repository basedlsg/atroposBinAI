#!/usr/bin/env python3
"""
Update LLM Integration with Groq Provider
"""

import os
import shutil
from pathlib import Path

def main():
    """Update the LLM integration with Groq support"""
    
    print("🔧 UPDATING LLM INTEGRATION WITH GROQ")
    print("=" * 60)
    
    # Backup original if it exists
    original_path = Path('llm_integration.py')
    backup_path = Path('llm_integration_backup.py')
    
    if original_path.exists():
        shutil.copy2(original_path, backup_path)
        print(f"✅ Backed up original to {backup_path}")
    
    # Create the updated integration
    updated_code = '''#!/usr/bin/env python3
"""
LLM Integration Module with Groq Support
"""

import os
import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    GROQ = "groq"
    MOCK = "mock"

@dataclass
class LLMRequest:
    agent_id: str
    prompt: str
    context: Dict[str, Any]
    max_tokens: int = 150
    temperature: float = 0.7

@dataclass
class LLMResponse:
    success: bool
    response: str = ""
    error: str = ""
    provider: str = ""
    model: str = ""
    response_time: float = 0.0
    tokens_used: int = 0

class GroqProvider:
    """Groq Llama provider - FREE and FAST"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.groq.com/openai/v1/chat/completions'
        self.models = {
            'fast': 'llama-3.1-8b-instant',
            'smart': 'llama-3.3-70b-versatile',
            'default': 'llama-3.1-8b-instant'
        }
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def make_request(self, request: LLMRequest, model: str = None) -> LLMResponse:
        """Make request to Groq API"""
        
        if not self.is_available():
            return LLMResponse(
                success=False,
                error="Groq API key not configured",
                provider="groq"
            )
        
        model = model or self.models['default']
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': request.prompt}],
            'max_tokens': request.max_tokens,
            'temperature': request.temperature
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    tokens_used = data.get('usage', {}).get('total_tokens', 0)
                    
                    return LLMResponse(
                        success=True,
                        response=content.strip(),
                        provider="groq",
                        model=model,
                        response_time=response_time,
                        tokens_used=tokens_used
                    )
                else:
                    return LLMResponse(
                        success=False,
                        error="No choices in response",
                        provider="groq",
                        response_time=response_time
                    )
            else:
                return LLMResponse(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    provider="groq",
                    response_time=response_time
                )
                
        except Exception as e:
            return LLMResponse(
                success=False,
                error=f"Request failed: {str(e)}",
                provider="groq",
                response_time=time.time() - start_time
            )

class MockProvider:
    """Mock provider for fallback"""
    
    def is_available(self) -> bool:
        return True
    
    async def make_request(self, request: LLMRequest, model: str = None) -> LLMResponse:
        agent_type = request.context.get('agent_type', 'agent')
        
        if "trader" in agent_type.lower():
            response = "I'll evaluate the trading opportunities and make a strategic decision."
        elif "scholar" in agent_type.lower():
            response = "I'll analyze the situation and prioritize knowledge preservation."
        elif "warrior" in agent_type.lower():
            response = "I'll assess threats and take action to protect the community."
        else:
            response = "I'll consider my options and make the best decision."
        
        return LLMResponse(
            success=True,
            response=response,
            provider="mock",
            model="rule-based"
        )

class LLMManager:
    """Enhanced LLM Manager with Groq support"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.GROQ):
        self.provider = provider
        self.client = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the selected provider"""
        
        if self.provider == LLMProvider.GROQ:
            api_key = os.getenv('GROQ_API_KEY')
            if api_key:
                self.client = GroqProvider(api_key)
                logger.info("✅ Groq Llama client initialized")
            else:
                logger.warning("❌ GROQ_API_KEY not found, falling back to mock")
                self.client = MockProvider()
        else:
            self.client = MockProvider()
    
    async def get_response(self, request: LLMRequest) -> LLMResponse:
        """Get LLM response"""
        
        if not self.client or not self.client.is_available():
            return LLMResponse(
                success=False,
                error="No available LLM provider",
                provider="none"
            )
        
        return await self.client.make_request(request)

def create_agent_prompt(context: Dict[str, Any]) -> str:
    """Create agent prompt from context"""
    
    agent_type = context.get('agent_type', 'agent')
    energy = context.get('energy', 0.5)
    happiness = context.get('happiness', 0.5)
    resources = context.get('resources', {})
    personality_traits = context.get('personality_traits', [])
    goals = context.get('goals', [])
    
    prompt = f"""You are a {agent_type} in a virtual society simulation.

Your current status:
- Energy: {energy:.2f} (0.0 = exhausted, 1.0 = fully energized)
- Happiness: {happiness:.2f} (0.0 = miserable, 1.0 = very happy)
- Resources: {resources}
- Personality: {', '.join(personality_traits)}
- Goals: {', '.join(goals)}

Based on your current situation, what do you decide to do next and why?
You can: work (gain resources), socialize (gain happiness), rest (gain energy), or explore.
Respond in 1-2 sentences as the character would think."""
    
    return prompt

async def test_groq_integration():
    """Test Groq integration"""
    
    print("🧪 Testing Groq Integration")
    print("=" * 40)
    
    test_context = {
        'id': 'test_agent',
        'agent_type': 'trader',
        'energy': 0.7,
        'happiness': 0.6,
        'resources': {'food': 25, 'currency': 150},
        'personality_traits': ['ambitious', 'social'],
        'goals': ['accumulate_wealth']
    }
    
    try:
        manager = LLMManager(provider=LLMProvider.GROQ)
        
        prompt = create_agent_prompt(test_context)
        request = LLMRequest(
            agent_id='test_agent',
            prompt=prompt,
            context=test_context
        )
        
        print("⏳ Making request...")
        
        response = await manager.get_response(request)
        
        if response.success:
            print(f"✅ Success!")
            print(f"   Response: {response.response}")
            print(f"   Provider: {response.provider}")
            print(f"   Response time: {response.response_time:.3f}s")
        else:
            print(f"❌ Failed: {response.error}")
        
        return response.success
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_groq_integration())
'''
    
    # Write the updated file
    with open('llm_integration.py', 'w') as f:
        f.write(updated_code)
    
    print("✅ Created updated llm_integration.py with Groq support")
    print("\n🎉 INTEGRATION UPDATE COMPLETE!")
    print("✅ Groq provider added")
    print("✅ FREE Llama models available")
    print("✅ Ready for testing")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Test with: python llm_integration.py")
    print("2. Integrate with simulation")

if __name__ == "__main__":
    main() 