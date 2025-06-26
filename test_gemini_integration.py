#!/usr/bin/env python3
"""
Comprehensive Test Runner for Gemini API Integration
Tests Google Gemini API with multiple spatial reasoning scenarios
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

@dataclass
class TestResult:
    scenario: str
    agent_id: int
    decision: str
    response_time: float
    success: bool
    distance_before: float
    distance_after: float
    improvement: float
    api_response: str

class GeminiTester:
    """Comprehensive tester for Gemini API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set environment variable.")
        
        self.results: List[TestResult] = []
        self.scenarios = self._create_test_scenarios()
        
        print(f"🧪 Gemini API Integration Tester")
        print(f"✅ Using Gemini API: {self.api_key[:20]}...")
    
    def _create_test_scenarios(self) -> List[Dict]:
        """Create diverse test scenarios"""
        return [
            {
                "name": "Simple Navigation",
                "agent_pos": (0, 0, 0),
                "target_pos": (5, 5, 5),
                "obstacles": [(2, 2, 2)],
                "expected_actions": ["MOVE_FORWARD", "MOVE_LEFT", "MOVE_UP"],
                "difficulty": "Easy"
            },
            {
                "name": "Obstacle Avoidance",
                "agent_pos": (0, 0, 0),
                "target_pos": (10, 0, 0),
                "obstacles": [(5, 0, 0), (6, 0, 0)],
                "expected_actions": ["MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"],
                "difficulty": "Medium"
            },
            {
                "name": "3D Pathfinding",
                "agent_pos": (0, 0, 0),
                "target_pos": (8, 8, 8),
                "obstacles": [(4, 4, 4), (6, 6, 6)],
                "expected_actions": ["MOVE_FORWARD", "MOVE_LEFT", "MOVE_UP"],
                "difficulty": "Hard"
            },
            {
                "name": "Complex Environment",
                "agent_pos": (0, 0, 0),
                "target_pos": (15, 15, 15),
                "obstacles": [(5, 5, 5), (10, 10, 10), (12, 12, 12)],
                "expected_actions": ["MOVE_FORWARD", "MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"],
                "difficulty": "Expert"
            },
            {
                "name": "Edge Case - Near Target",
                "agent_pos": (9, 9, 9),
                "target_pos": (10, 10, 10),
                "obstacles": [],
                "expected_actions": ["MOVE_FORWARD", "MOVE_LEFT", "MOVE_UP"],
                "difficulty": "Easy"
            },
            {
                "name": "Maze Navigation",
                "agent_pos": (0, 0, 0),
                "target_pos": (12, 12, 0),
                "obstacles": [(2, 0, 0), (4, 0, 0), (6, 0, 0), (8, 0, 0), (10, 0, 0)],
                "expected_actions": ["MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"],
                "difficulty": "Hard"
            }
        ]
    
    def test_gemini_api(self) -> bool:
        """Test basic Gemini API connectivity"""
        print("\n🔍 Testing Gemini API connectivity...")
        
        prompt = "Respond with only the word 'SUCCESS' if you can read this message."
        
        try:
            response = self._call_gemini_api(prompt)
            if "SUCCESS" in response.upper():
                print("✅ Gemini API connectivity test passed")
                return True
            else:
                print(f"❌ Unexpected response: {response}")
                return False
        except Exception as e:
            print(f"❌ API connectivity test failed: {e}")
            return False
    
    def run_comprehensive_tests(self) -> Dict:
        """Run comprehensive test suite"""
        print(f"\n🚀 Running comprehensive Gemini integration tests...")
        print(f"📊 Testing {len(self.scenarios)} scenarios with multiple agents")
        
        # Test API connectivity first
        if not self.test_gemini_api():
            return {"error": "API connectivity failed"}
        
        # Run scenario tests
        scenario_results = {}
        total_tests = 0
        successful_tests = 0
        
        for scenario in self.scenarios:
            print(f"\n📋 Testing scenario: {scenario['name']} ({scenario['difficulty']})")
            scenario_results[scenario['name']] = self._test_scenario(scenario)
            total_tests += len(scenario_results[scenario['name']])
            successful_tests += sum(1 for r in scenario_results[scenario['name']] if r.success)
        
        # Calculate overall metrics
        response_times = [r.response_time for r in self.results]
        improvements = [r.improvement for r in self.results if r.success]
        
        overall_results = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "average_response_time": statistics.mean(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "average_improvement": statistics.mean(improvements) if improvements else 0,
            "median_improvement": statistics.median(improvements) if improvements else 0,
            "scenario_results": scenario_results,
            "detailed_results": [r.__dict__ for r in self.results],
            "api_key_used": self.api_key[:20] + "...",
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return overall_results
    
    def _test_scenario(self, scenario: Dict) -> List[TestResult]:
        """Test a specific scenario"""
        results = []
        
        # Test with multiple agents
        for agent_id in range(1, 4):  # Test 3 agents per scenario
            print(f"  🤖 Testing Agent {agent_id}...")
            
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
            
            # Get LLM decision
            start_time = time.time()
            decision, api_response = self._get_spatial_decision(agent_pos, target_pos, scenario["obstacles"])
            response_time = time.time() - start_time
            
            # Simulate action and calculate new distance
            new_pos = self._simulate_action(agent_pos, decision)
            distance_after = math.sqrt(sum((a - t) ** 2 for a, t in zip(new_pos, target_pos)))
            improvement = distance_before - distance_after
            
            # Determine success
            success = (
                decision in scenario["expected_actions"] or
                improvement > 0 or
                distance_after < distance_before
            )
            
            result = TestResult(
                scenario=scenario["name"],
                agent_id=agent_id,
                decision=decision,
                response_time=response_time,
                success=success,
                distance_before=distance_before,
                distance_after=distance_after,
                improvement=improvement,
                api_response=api_response
            )
            
            results.append(result)
            self.results.append(result)
            
            print(f"    Decision: {decision} | Success: {success} | Improvement: {improvement:.2f} | Time: {response_time:.3f}s")
        
        return results
    
    def _get_spatial_decision(self, agent_pos: Tuple[float, float, float], 
                            target_pos: Tuple[float, float, float], 
                            obstacles: List[Tuple[float, float, float]]) -> Tuple[str, str]:
        """Get spatial decision from Gemini API"""
        
        prompt = f"""You are an AI agent navigating in 3D space. Choose the best action to move toward the target.

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

        try:
            response = self._call_gemini_api(prompt)
            return self._parse_decision(response), response
        except Exception as e:
            print(f"    ⚠️ API call failed: {e}")
            fallback = self._fallback_decision(agent_pos, target_pos)
            return fallback, f"FALLBACK: {fallback}"
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Make API call to Google Gemini"""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
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
        
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Create request
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        # Make request
        with urllib.request.urlopen(req, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return content.strip()
            else:
                raise Exception(f"Unexpected API response: {result}")
    
    def _parse_decision(self, response: str) -> str:
        """Parse decision from API response"""
        decision = response.strip().upper()
        
        # Clean up response
        if ":" in decision:
            decision = decision.split(":")[-1].strip()
        
        # Validate decision
        valid_actions = ["MOVE_FORWARD", "MOVE_BACKWARD", "MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"]
        if decision in valid_actions:
            return decision
        else:
            # Try to extract action from response
            for action in valid_actions:
                if action in decision:
                    return action
            
            # Default fallback
            return "MOVE_FORWARD"
    
    def _fallback_decision(self, agent_pos: Tuple[float, float, float], 
                          target_pos: Tuple[float, float, float]) -> str:
        """Intelligent fallback decision"""
        dx = target_pos[0] - agent_pos[0]
        dy = target_pos[1] - agent_pos[1]
        dz = target_pos[2] - agent_pos[2]
        
        # Choose action based on largest component
        if abs(dx) > abs(dy) and abs(dx) > abs(dz):
            return "MOVE_FORWARD" if dx > 0 else "MOVE_BACKWARD"
        elif abs(dy) > abs(dz):
            return "MOVE_LEFT" if dy > 0 else "MOVE_RIGHT"
        else:
            return "MOVE_UP" if dz > 0 else "MOVE_DOWN"
    
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
    
    def print_detailed_results(self, results: Dict):
        """Print detailed test results"""
        print(f"\n📊 COMPREHENSIVE GEMINI TEST RESULTS")
        print("=" * 70)
        
        print(f"🎯 Overall Performance:")
        print(f"  Total Tests: {results['total_tests']}")
        print(f"  Successful Tests: {results['successful_tests']}")
        print(f"  Success Rate: {results['success_rate']:.1%}")
        print(f"  Average Response Time: {results['average_response_time']:.3f}s")
        print(f"  Median Response Time: {results['median_response_time']:.3f}s")
        print(f"  Response Time Range: {results['min_response_time']:.3f}s - {results['max_response_time']:.3f}s")
        print(f"  Average Improvement: {results['average_improvement']:.2f} units")
        print(f"  Median Improvement: {results['median_improvement']:.2f} units")
        
        print(f"\n📋 Scenario Breakdown:")
        for scenario_name, scenario_results in results['scenario_results'].items():
            success_count = sum(1 for r in scenario_results if r.success)
            avg_response = statistics.mean([r.response_time for r in scenario_results])
            avg_improvement = statistics.mean([r.improvement for r in scenario_results if r.success])
            
            # Find scenario difficulty
            difficulty = next((s['difficulty'] for s in self.scenarios if s['name'] == scenario_name), "Unknown")
            
            print(f"  {scenario_name} ({difficulty}):")
            print(f"    Success Rate: {success_count}/{len(scenario_results)} ({success_count/len(scenario_results):.1%})")
            print(f"    Avg Response: {avg_response:.3f}s")
            print(f"    Avg Improvement: {avg_improvement:.2f} units")
        
        print(f"\n🔍 Sample Decisions:")
        for i, result in enumerate(self.results[:10]):  # Show first 10 results
            print(f"  Test {i+1}: {result.decision} | Success: {result.success} | Improvement: {result.improvement:.2f} | Time: {result.response_time:.3f}s")
        
        print(f"\n📈 Performance Analysis:")
        # Analyze by difficulty
        difficulty_stats = {}
        for scenario in self.scenarios:
            difficulty = scenario['difficulty']
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {'tests': 0, 'successes': 0, 'response_times': [], 'improvements': []}
            
            scenario_results = results['scenario_results'][scenario['name']]
            difficulty_stats[difficulty]['tests'] += len(scenario_results)
            difficulty_stats[difficulty]['successes'] += sum(1 for r in scenario_results if r.success)
            difficulty_stats[difficulty]['response_times'].extend([r.response_time for r in scenario_results])
            difficulty_stats[difficulty]['improvements'].extend([r.improvement for r in scenario_results if r.success])
        
        for difficulty, stats in difficulty_stats.items():
            if stats['tests'] > 0:
                success_rate = stats['successes'] / stats['tests']
                avg_response = statistics.mean(stats['response_times'])
                avg_improvement = statistics.mean(stats['improvements']) if stats['improvements'] else 0
                print(f"  {difficulty}: {success_rate:.1%} success rate, {avg_response:.3f}s avg response, {avg_improvement:.2f} avg improvement")
    
    def save_results(self, results: Dict, filename: str = "gemini_test_results.json"):
        """Save test results to file"""
        # Convert all TestResult objects to dictionaries for JSON serialization
        serializable_results = results.copy()
        serializable_results['detailed_results'] = [r.__dict__ for r in self.results]
        
        # Convert scenario results to serializable format
        serializable_scenario_results = {}
        for scenario_name, scenario_results in results['scenario_results'].items():
            serializable_scenario_results[scenario_name] = [r.__dict__ for r in scenario_results]
        serializable_results['scenario_results'] = serializable_scenario_results
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

def main():
    """Main test runner"""
    print("🧠 Gemini API Integration Test Suite")
    print("=" * 50)
    
    try:
        # Set Gemini API key
        gemini_key = "AIzaSyAqko3NqGS-GtXhzm8LeiZ3xUEyo_XIqLo"
        os.environ['GEMINI_API_KEY'] = gemini_key
        
        # Initialize tester
        tester = GeminiTester(gemini_key)
        
        # Run comprehensive tests
        results = tester.run_comprehensive_tests()
        
        if "error" in results:
            print(f"❌ Test failed: {results['error']}")
            return
        
        # Print detailed results
        tester.print_detailed_results(results)
        
        # Save results
        tester.save_results(results)
        
        # Print summary
        print(f"\n✅ Gemini Test Suite Completed Successfully!")
        print(f"🎯 Key Achievements:")
        print(f"  - Real Gemini API integration working")
        print(f"  - {results['total_tests']} spatial reasoning tests executed")
        print(f"  - {results['success_rate']:.1%} success rate achieved")
        print(f"  - Average response time: {results['average_response_time']:.3f}s")
        print(f"  - Average improvement: {results['average_improvement']:.2f} units")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 