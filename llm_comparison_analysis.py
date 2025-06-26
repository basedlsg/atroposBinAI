#!/usr/bin/env python3
"""
LLM Comparison Analysis Tool
Compares different LLM providers for spatial reasoning tasks
"""

import os
import json
import time
import random
import math
import urllib.request
import urllib.parse
import urllib.error
import ssl
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import statistics
from datetime import datetime

@dataclass
class LLMResult:
    provider: str
    model: str
    scenario: str
    decision: str
    response_time: float
    success: bool
    improvement: float
    cost_estimate: float
    api_response: str

class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.provider_name = "Unknown"
    
    def get_spatial_decision(self, prompt: str) -> Tuple[str, str, float]:
        """Get spatial decision from LLM"""
        raise NotImplementedError
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for API call"""
        return 0.0

class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__(api_key, model)
        self.provider_name = "Gemini"
    
    def get_spatial_decision(self, prompt: str) -> Tuple[str, str, float]:
        """Get spatial decision from Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 50,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            response_time = time.time() - start_time
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return content.strip(), content.strip(), response_time
            else:
                raise Exception(f"Unexpected API response: {result}")
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for Gemini API call"""
        # Gemini 1.5 Flash pricing (approximate)
        return tokens * 0.000075 / 1000  # $0.075 per 1M tokens

class OpenAIProvider(LLMProvider):
    """OpenAI provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model)
        self.provider_name = "OpenAI"
    
    def get_spatial_decision(self, prompt: str) -> Tuple[str, str, float]:
        """Get spatial decision from OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        
        data = {
            "model": self.model,
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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            response_time = time.time() - start_time
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content.strip(), content.strip(), response_time
            else:
                raise Exception(f"Unexpected API response: {result}")
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for OpenAI API call"""
        # GPT-3.5-turbo pricing (approximate)
        return tokens * 0.0005 / 1000  # $0.50 per 1M tokens

class LLMComparisonAnalyzer:
    """Analyzer for comparing different LLM providers"""
    
    def __init__(self):
        self.providers = {}
        self.results: List[LLMResult] = []
        self.scenarios = self._create_test_scenarios()
        
        print("🔬 LLM Comparison Analysis Tool")
        print("=" * 50)
    
    def _create_test_scenarios(self) -> List[Dict]:
        """Create test scenarios for comparison"""
        return [
            {
                "name": "Simple Navigation",
                "agent_pos": (0, 0, 0),
                "target_pos": (5, 5, 5),
                "obstacles": [(2, 2, 2)],
                "difficulty": "Easy",
                "expected_actions": ["MOVE_FORWARD", "MOVE_LEFT", "MOVE_UP"]
            },
            {
                "name": "Obstacle Avoidance",
                "agent_pos": (0, 0, 0),
                "target_pos": (10, 0, 0),
                "obstacles": [(5, 0, 0), (6, 0, 0)],
                "difficulty": "Medium",
                "expected_actions": ["MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"]
            },
            {
                "name": "3D Pathfinding",
                "agent_pos": (0, 0, 0),
                "target_pos": (8, 8, 8),
                "obstacles": [(4, 4, 4), (6, 6, 6)],
                "difficulty": "Hard",
                "expected_actions": ["MOVE_FORWARD", "MOVE_LEFT", "MOVE_UP"]
            },
            {
                "name": "Complex Environment",
                "agent_pos": (0, 0, 0),
                "target_pos": (15, 15, 15),
                "obstacles": [(5, 5, 5), (10, 10, 10), (12, 12, 12)],
                "difficulty": "Expert",
                "expected_actions": ["MOVE_FORWARD", "MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"]
            }
        ]
    
    def add_provider(self, provider: LLMProvider):
        """Add an LLM provider to the comparison"""
        self.providers[provider.provider_name] = provider
        print(f"✅ Added {provider.provider_name} ({provider.model})")
    
    def run_comparison(self) -> Dict:
        """Run comprehensive comparison of all providers"""
        print(f"\n🚀 Running LLM comparison analysis...")
        print(f"📊 Testing {len(self.providers)} providers across {len(self.scenarios)} scenarios")
        
        # Test each provider
        for provider_name, provider in self.providers.items():
            print(f"\n🔍 Testing {provider_name}...")
            
            # Test connectivity first
            if not self._test_provider_connectivity(provider):
                print(f"❌ {provider_name} connectivity test failed")
                continue
            
            # Run scenarios
            for scenario in self.scenarios:
                print(f"  📋 Testing scenario: {scenario['name']} ({scenario['difficulty']})")
                
                # Test multiple times for statistical significance
                for test_id in range(3):
                    try:
                        result = self._test_scenario(provider, scenario, test_id)
                        self.results.append(result)
                        print(f"    Test {test_id + 1}: {result.decision} | Success: {result.success} | Time: {result.response_time:.3f}s")
                    except Exception as e:
                        print(f"    Test {test_id + 1}: Failed - {e}")
        
        return self._analyze_results()
    
    def _test_provider_connectivity(self, provider: LLMProvider) -> bool:
        """Test basic connectivity for a provider"""
        try:
            prompt = "Respond with only the word 'SUCCESS' if you can read this message."
            response, _, _ = provider.get_spatial_decision(prompt)
            return "SUCCESS" in response.upper()
        except Exception as e:
            print(f"    ⚠️ Connectivity test failed: {e}")
            return False
    
    def _test_scenario(self, provider: LLMProvider, scenario: Dict, test_id: int) -> LLMResult:
        """Test a specific scenario with a provider"""
        
        # Create agent position with slight variations
        base_pos = scenario["agent_pos"]
        agent_pos = (
            base_pos[0] + random.uniform(-0.5, 0.5),
            base_pos[1] + random.uniform(-0.5, 0.5),
            base_pos[2] + random.uniform(-0.5, 0.5)
        )
        
        # Calculate distances
        target_pos = scenario["target_pos"]
        distance_before = math.sqrt(sum((a - t) ** 2 for a, t in zip(agent_pos, target_pos)))
        
        # Create prompt
        prompt = self._create_spatial_prompt(agent_pos, target_pos, scenario["obstacles"])
        
        # Get LLM decision
        decision, api_response, response_time = provider.get_spatial_decision(prompt)
        
        # Parse decision
        parsed_decision = self._parse_decision(decision)
        
        # Simulate action and calculate improvement
        new_pos = self._simulate_action(agent_pos, parsed_decision)
        distance_after = math.sqrt(sum((a - t) ** 2 for a, t in zip(new_pos, target_pos)))
        improvement = distance_before - distance_after
        
        # Determine success
        success = (
            parsed_decision in scenario["expected_actions"] or
            improvement > 0 or
            distance_after < distance_before
        )
        
        # Estimate cost
        cost_estimate = provider.estimate_cost(len(prompt.split()) + len(decision.split()))
        
        return LLMResult(
            provider=provider.provider_name,
            model=provider.model,
            scenario=scenario["name"],
            decision=parsed_decision,
            response_time=response_time,
            success=success,
            improvement=improvement,
            cost_estimate=cost_estimate,
            api_response=api_response
        )
    
    def _create_spatial_prompt(self, agent_pos: Tuple[float, float, float], 
                             target_pos: Tuple[float, float, float], 
                             obstacles: List[Tuple[float, float, float]]) -> str:
        """Create a spatial reasoning prompt"""
        
        return f"""You are an AI agent navigating in 3D space. Choose the best action to move toward the target.

CURRENT SITUATION:
- Your position: ({agent_pos[0]:.1f}, {agent_pos[1]:.1f}, {agent_pos[2]:.1f})
- Target position: ({target_pos[0]:.1f}, {target_pos[1]:.1f}, {target_pos[2]:.1f})
- Distance to target: {math.sqrt(sum((a - t) ** 2 for a, t in zip(agent_pos, target_pos))):.1f}

OBSTACLES (avoid these):
{chr(10).join([f"- Obstacle {i+1}: ({obs[0]:.1f}, {obs[1]:.1f}, {obs[2]:.1f})" for i, obs in enumerate(obstacles)])}

AVAILABLE ACTIONS:
- MOVE_FORWARD (increase X)
- MOVE_BACKWARD (decrease X)
- MOVE_LEFT (increase Y)
- MOVE_RIGHT (decrease Y)
- MOVE_UP (increase Z)
- MOVE_DOWN (decrease Z)

Choose the action that moves you closest to the target while avoiding obstacles. Respond with ONLY the action name."""
    
    def _parse_decision(self, response: str) -> str:
        """Parse decision from API response"""
        decision = response.strip().upper()
        
        if ":" in decision:
            decision = decision.split(":")[-1].strip()
        
        valid_actions = ["MOVE_FORWARD", "MOVE_BACKWARD", "MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"]
        if decision in valid_actions:
            return decision
        
        for action in valid_actions:
            if action in decision:
                return action
        
        return "MOVE_FORWARD"
    
    def _simulate_action(self, position: Tuple[float, float, float], action: str) -> Tuple[float, float, float]:
        """Simulate the result of an action"""
        x, y, z = position
        
        if action == "MOVE_FORWARD":
            return (x + 1, y, z)
        elif action == "MOVE_BACKWARD":
            return (x - 1, y, z)
        elif action == "MOVE_LEFT":
            return (x, y + 1, z)
        elif action == "MOVE_RIGHT":
            return (x, y - 1, z)
        elif action == "MOVE_UP":
            return (x, y, z + 1)
        elif action == "MOVE_DOWN":
            return (x, y, z - 1)
        else:
            return position
    
    def _analyze_results(self) -> Dict:
        """Analyze comparison results"""
        if not self.results:
            return {"error": "No results to analyze"}
        
        # Group results by provider
        provider_results = {}
        for result in self.results:
            if result.provider not in provider_results:
                provider_results[result.provider] = []
            provider_results[result.provider].append(result)
        
        # Calculate metrics for each provider
        provider_metrics = {}
        for provider, results in provider_results.items():
            response_times = [r.response_time for r in results]
            improvements = [r.improvement for r in results if r.success]
            costs = [r.cost_estimate for r in results]
            
            provider_metrics[provider] = {
                "total_tests": len(results),
                "successful_tests": sum(1 for r in results if r.success),
                "success_rate": sum(1 for r in results if r.success) / len(results),
                "average_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "average_improvement": statistics.mean(improvements) if improvements else 0,
                "median_improvement": statistics.median(improvements) if improvements else 0,
                "total_cost": sum(costs),
                "average_cost": statistics.mean(costs),
                "model": results[0].model if results else "Unknown"
            }
        
        # Calculate overall comparison metrics
        overall_analysis = {
            "total_tests": len(self.results),
            "providers_tested": list(provider_results.keys()),
            "provider_metrics": provider_metrics,
            "best_performance": self._find_best_performer(provider_metrics),
            "cost_analysis": self._analyze_costs(provider_metrics),
            "speed_analysis": self._analyze_speed(provider_metrics),
            "accuracy_analysis": self._analyze_accuracy(provider_metrics),
            "detailed_results": [r.__dict__ for r in self.results],
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return overall_analysis
    
    def _find_best_performer(self, provider_metrics: Dict) -> Dict:
        """Find the best performing provider"""
        best_provider = None
        best_score = 0
        
        for provider, metrics in provider_metrics.items():
            # Calculate composite score (success rate * improvement / response time)
            score = (metrics["success_rate"] * metrics["average_improvement"]) / max(metrics["average_response_time"], 0.001)
            
            if score > best_score:
                best_score = score
                best_provider = provider
        
        return {
            "provider": best_provider,
            "score": best_score,
            "metrics": provider_metrics[best_provider] if best_provider else {}
        }
    
    def _analyze_costs(self, provider_metrics: Dict) -> Dict:
        """Analyze cost efficiency"""
        costs = [(provider, metrics["average_cost"]) for provider, metrics in provider_metrics.items()]
        costs.sort(key=lambda x: x[1])
        
        return {
            "cheapest": costs[0] if costs else None,
            "most_expensive": costs[-1] if costs else None,
            "cost_comparison": costs
        }
    
    def _analyze_speed(self, provider_metrics: Dict) -> Dict:
        """Analyze speed performance"""
        speeds = [(provider, metrics["average_response_time"]) for provider, metrics in provider_metrics.items()]
        speeds.sort(key=lambda x: x[1])
        
        return {
            "fastest": speeds[0] if speeds else None,
            "slowest": speeds[-1] if speeds else None,
            "speed_comparison": speeds
        }
    
    def _analyze_accuracy(self, provider_metrics: Dict) -> Dict:
        """Analyze accuracy performance"""
        accuracies = [(provider, metrics["success_rate"]) for provider, metrics in provider_metrics.items()]
        accuracies.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "most_accurate": accuracies[0] if accuracies else None,
            "least_accurate": accuracies[-1] if accuracies else None,
            "accuracy_comparison": accuracies
        }
    
    def print_comparison_results(self, results: Dict):
        """Print detailed comparison results"""
        print(f"\n📊 LLM COMPARISON RESULTS")
        print("=" * 70)
        
        if "error" in results:
            print(f"❌ Analysis failed: {results['error']}")
            return
        
        print(f"🎯 Overall Analysis:")
        print(f"  Total Tests: {results['total_tests']}")
        print(f"  Providers Tested: {', '.join(results['providers_tested'])}")
        
        print(f"\n🏆 Best Performer:")
        best = results['best_performance']
        print(f"  Provider: {best['provider']}")
        print(f"  Composite Score: {best['score']:.3f}")
        print(f"  Success Rate: {best['metrics']['success_rate']:.1%}")
        print(f"  Avg Response Time: {best['metrics']['average_response_time']:.3f}s")
        print(f"  Avg Improvement: {best['metrics']['average_improvement']:.2f} units")
        
        print(f"\n📈 Provider Performance Breakdown:")
        for provider, metrics in results['provider_metrics'].items():
            print(f"  {provider} ({metrics['model']}):")
            print(f"    Success Rate: {metrics['success_rate']:.1%}")
            print(f"    Avg Response Time: {metrics['average_response_time']:.3f}s")
            print(f"    Avg Improvement: {metrics['average_improvement']:.2f} units")
            print(f"    Total Cost: ${metrics['total_cost']:.6f}")
        
        print(f"\n💰 Cost Analysis:")
        cost_analysis = results['cost_analysis']
        if cost_analysis['cheapest']:
            print(f"  Cheapest: {cost_analysis['cheapest'][0]} (${cost_analysis['cheapest'][1]:.6f} per call)")
        if cost_analysis['most_expensive']:
            print(f"  Most Expensive: {cost_analysis['most_expensive'][0]} (${cost_analysis['most_expensive'][1]:.6f} per call)")
        
        print(f"\n⚡ Speed Analysis:")
        speed_analysis = results['speed_analysis']
        if speed_analysis['fastest']:
            print(f"  Fastest: {speed_analysis['fastest'][0]} ({speed_analysis['fastest'][1]:.3f}s)")
        if speed_analysis['slowest']:
            print(f"  Slowest: {speed_analysis['slowest'][0]} ({speed_analysis['slowest'][1]:.3f}s)")
        
        print(f"\n🎯 Accuracy Analysis:")
        accuracy_analysis = results['accuracy_analysis']
        if accuracy_analysis['most_accurate']:
            print(f"  Most Accurate: {accuracy_analysis['most_accurate'][0]} ({accuracy_analysis['most_accurate'][1]:.1%})")
        if accuracy_analysis['least_accurate']:
            print(f"  Least Accurate: {accuracy_analysis['least_accurate'][0]} ({accuracy_analysis['least_accurate'][1]:.1%})")
    
    def save_results(self, results: Dict, filename: str = "llm_comparison_results.json"):
        """Save comparison results to file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

def main():
    """Main comparison runner"""
    print("🔬 LLM Comparison Analysis")
    print("=" * 50)
    
    try:
        # Initialize analyzer
        analyzer = LLMComparisonAnalyzer()
        
        # Add providers
        gemini_key = "AIzaSyAqko3NqGS-GtXhzm8LeiZ3xUEyo_XIqLo"
        openai_key = "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"
        
        analyzer.add_provider(GeminiProvider(gemini_key))
        analyzer.add_provider(OpenAIProvider(openai_key))
        
        # Run comparison
        results = analyzer.run_comparison()
        
        if "error" in results:
            print(f"❌ Comparison failed: {results['error']}")
            return
        
        # Print results
        analyzer.print_comparison_results(results)
        
        # Save results
        analyzer.save_results(results)
        
        print(f"\n✅ LLM Comparison Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 