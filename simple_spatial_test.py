#!/usr/bin/env python3
"""
Simple Spatial Reasoning Test
Uses only standard library modules to test LLM spatial reasoning
"""

import json
import time
import os
import sys
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleSpatialTestRunner:
    """Simple test runner using only standard library"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.base_url = 'https://api.groq.com/openai/v1/chat/completions'
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_response_time': 0.0
        }
    
    def test_single_spatial_reasoning(self, agent_id: str, scenario: str) -> dict:
        """Test single agent on spatial reasoning task"""
        
        # Create test environment
        environment = self._create_test_environment(scenario)
        
        # Get start and target positions
        start_pos = environment['start']
        target_pos = environment['target']
        obstacles = environment.get('obstacles', [])
        
        # Calculate optimal path length
        optimal_distance = ((target_pos[0] - start_pos[0])**2 + (target_pos[1] - start_pos[1])**2)**0.5
        
        # Run navigation simulation
        current_pos = list(start_pos)
        path_taken = [current_pos.copy()]
        collisions = 0
        total_response_time = 0.0
        total_tokens = 0
        decisions = []
        
        max_steps = 20  # Reduced for faster testing
        target_reached = False
        
        for step in range(max_steps):
            # Create prompt for this step
            prompt = self._create_navigation_prompt(
                agent_id, current_pos, target_pos, obstacles, step
            )
            
            # Make API call
            start_time = time.time()
            response = self._make_groq_request(prompt)
            response_time = time.time() - start_time
            
            total_response_time += response_time
            total_tokens += response.get('tokens_used', 0)
            
            if response['success']:
                # Parse decision
                decision = self._parse_decision(response['content'])
                decisions.append({
                    'step': step,
                    'action': decision['action'],
                    'reasoning': decision['reasoning'],
                    'response_time': response_time,
                    'tokens_used': response.get('tokens_used', 0)
                })
                
                # Calculate next position
                next_pos = self._calculate_next_position(current_pos, decision['action'])
                
                # Check for collisions
                if self._check_collision(next_pos, obstacles):
                    collisions += 1
                    # Try to find alternative path
                    next_pos = self._find_alternative_path(current_pos, target_pos, obstacles)
                
                # Update position
                current_pos = next_pos
                path_taken.append(current_pos.copy())
                
                # Check if target reached
                distance_to_target = ((current_pos[0] - target_pos[0])**2 + (current_pos[1] - target_pos[1])**2)**0.5
                if distance_to_target < 1.0:
                    target_reached = True
                    break
            else:
                logger.warning(f"API request failed for {agent_id} at step {step}: {response.get('error', 'Unknown error')}")
                break
        
        # Calculate metrics
        actual_path_length = self._calculate_path_length(path_taken)
        path_efficiency = optimal_distance / actual_path_length if actual_path_length > 0 else 0
        
        obstacle_avoidance_rate = 1.0 - (collisions / max(len(obstacles), 1))
        task_completion_rate = 1.0 if target_reached else 0.0
        
        # Calculate spatial understanding score
        spatial_understanding_score = (
            path_efficiency * 0.3 +
            obstacle_avoidance_rate * 0.25 +
            (1.0 - collisions / max(1, len(path_taken))) * 0.2 +
            task_completion_rate * 0.15 +
            (1.0 - total_response_time / 60.0) * 0.1
        )
        
        result = {
            'agent_id': agent_id,
            'scenario': scenario,
            'target_reached': target_reached,
            'path_taken': path_taken,
            'final_position': current_pos,
            'total_steps': len(path_taken),
            'collisions': collisions,
            'path_efficiency': path_efficiency,
            'obstacle_avoidance_rate': obstacle_avoidance_rate,
            'task_completion_rate': task_completion_rate,
            'spatial_understanding_score': spatial_understanding_score,
            'total_response_time': total_response_time,
            'total_tokens': total_tokens,
            'decisions': decisions
        }
        
        return result
    
    def _create_test_environment(self, scenario: str) -> dict:
        """Create test environment for given scenario"""
        
        environments = {
            'simple_navigation': {
                'start': (0, 0),
                'target': (8, 8),
                'obstacles': [],
                'description': 'Navigate from start to target without obstacles'
            },
            'obstacle_avoidance': {
                'start': (0, 0),
                'target': (12, 12),
                'obstacles': [
                    {'position': (4, 4), 'radius': 1.5},
                    {'position': (8, 6), 'radius': 1.0},
                    {'position': (6, 10), 'radius': 1.5}
                ],
                'description': 'Navigate around obstacles to reach target'
            },
            'spatial_memory': {
                'start': (0, 0),
                'target': (10, 10),
                'obstacles': [],
                'resources': [
                    {'position': (6, 4), 'type': 'resource'},
                    {'position': (8, 2), 'type': 'resource'}
                ],
                'description': 'Remember and navigate to previously seen resources'
            }
        }
        
        return environments.get(scenario, environments['simple_navigation'])
    
    def _create_navigation_prompt(self, agent_id: str, current_pos: list, target_pos: tuple, 
                                 obstacles: list, step: int) -> str:
        """Create navigation prompt for LLM"""
        
        prompt = f"""You are Agent {agent_id} navigating in a 2D environment.

CURRENT SITUATION (Step {step + 1}):
- Your current position: ({current_pos[0]:.1f}, {current_pos[1]:.1f})
- Target position: ({target_pos[0]:.1f}, {target_pos[1]:.1f})
- Distance to target: {((target_pos[0] - current_pos[0])**2 + (target_pos[1] - current_pos[1])**2)**0.5:.2f} units

AVAILABLE ACTIONS:
- move_north: Move 1 unit north (+Y direction)
- move_south: Move 1 unit south (-Y direction)
- move_east: Move 1 unit east (+X direction)
- move_west: Move 1 unit west (-X direction)
- move_northeast: Move diagonally northeast
- move_northwest: Move diagonally northwest
- move_southeast: Move diagonally southeast
- move_southwest: Move diagonally southwest

INSTRUCTIONS:
1. Analyze the spatial relationship between your position and the target
2. Choose the most efficient action to move toward the target
3. Avoid obstacles if present
4. Respond with valid JSON only

Respond with JSON: {{"action": "move_direction", "reasoning": "brief explanation"}}"""

        return prompt
    
    def _make_groq_request(self, prompt: str) -> dict:
        """Make request to Groq API using standard library"""
        
        headers = {
            'Authorization': f'Bearer {self.groq_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'llama-3.1-8b-instant',
            'messages': [
                {'role': 'system', 'content': 'You are an AI agent navigating in a 2D environment. Respond with valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 150,
            'temperature': 0.7
        }
        
        self.stats['total_requests'] += 1
        
        try:
            # Create request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.base_url,
                data=data,
                headers=headers,
                method='POST'
            )
            
            # Make request
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0]['message']['content'].strip()
                    tokens_used = response_data.get('usage', {}).get('total_tokens', 0)
                    
                    self.stats['successful_requests'] += 1
                    self.stats['total_tokens'] += tokens_used
                    
                    return {
                        'success': True,
                        'content': content,
                        'tokens_used': tokens_used
                    }
                else:
                    self.stats['failed_requests'] += 1
                    return {
                        'success': False,
                        'error': 'No choices in response'
                    }
                        
        except Exception as e:
            self.stats['failed_requests'] += 1
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
    
    def _parse_decision(self, content: str) -> dict:
        """Parse decision from LLM response"""
        
        try:
            # Try to parse JSON
            decision = json.loads(content)
            return {
                'action': decision.get('action', 'rest'),
                'reasoning': decision.get('reasoning', 'No reasoning provided')
            }
        except json.JSONDecodeError:
            # Fallback parsing
            content_upper = content.upper()
            actions = ['move_north', 'move_south', 'move_east', 'move_west', 
                      'move_northeast', 'move_northwest', 'move_southeast', 'move_southwest']
            
            for action in actions:
                if action.upper() in content_upper:
                    return {
                        'action': action,
                        'reasoning': f'Parsed from text: {content[:50]}...'
                    }
            
            return {
                'action': 'rest',
                'reasoning': f'Could not parse action from: {content[:50]}...'
            }
    
    def _calculate_next_position(self, current_pos: list, action: str) -> list:
        """Calculate next position based on action"""
        
        next_pos = current_pos.copy()
        
        if action == "move_north":
            next_pos[1] += 1.0
        elif action == "move_south":
            next_pos[1] -= 1.0
        elif action == "move_east":
            next_pos[0] += 1.0
        elif action == "move_west":
            next_pos[0] -= 1.0
        elif action == "move_northeast":
            next_pos[0] += 0.7
            next_pos[1] += 0.7
        elif action == "move_northwest":
            next_pos[0] -= 0.7
            next_pos[1] += 0.7
        elif action == "move_southeast":
            next_pos[0] += 0.7
            next_pos[1] -= 0.7
        elif action == "move_southwest":
            next_pos[0] -= 0.7
            next_pos[1] -= 0.7
        
        return next_pos
    
    def _check_collision(self, position: list, obstacles: list) -> bool:
        """Check if position collides with any obstacles"""
        
        for obstacle in obstacles:
            distance = ((position[0] - obstacle['position'][0])**2 + 
                       (position[1] - obstacle['position'][1])**2)**0.5
            if distance < obstacle['radius']:
                return True
        return False
    
    def _find_alternative_path(self, current_pos: list, target_pos: tuple, obstacles: list) -> list:
        """Find alternative path when collision detected"""
        
        # Simple avoidance: move perpendicular to obstacle
        for obstacle in obstacles:
            distance = ((current_pos[0] - obstacle['position'][0])**2 + 
                       (current_pos[1] - obstacle['position'][1])**2)**0.5
            if distance < obstacle['radius'] + 1.0:
                # Move away from obstacle
                dx = current_pos[0] - obstacle['position'][0]
                dy = current_pos[1] - obstacle['position'][1]
                length = (dx**2 + dy**2)**0.5
                if length > 0:
                    next_pos = [
                        current_pos[0] + dx/length,
                        current_pos[1] + dy/length
                    ]
                    return next_pos
        
        return current_pos
    
    def _calculate_path_length(self, path: list) -> float:
        """Calculate total path length"""
        
        total_length = 0.0
        for i in range(1, len(path)):
            segment_length = ((path[i][0] - path[i-1][0])**2 + (path[i][1] - path[i-1][1])**2)**0.5
            total_length += segment_length
        
        return total_length
    
    def run_comprehensive_test(self, num_agents: int = 5) -> dict:
        """Run comprehensive test with multiple agents and scenarios"""
        
        logger.info(f"Starting comprehensive spatial reasoning test with {num_agents} agents")
        
        scenarios = ['simple_navigation', 'obstacle_avoidance', 'spatial_memory']
        results = {
            'test_info': {
                'num_agents': num_agents,
                'scenarios': scenarios,
                'start_time': datetime.now().isoformat(),
                'api_key_configured': bool(self.groq_api_key)
            },
            'agent_results': [],
            'scenario_summaries': {},
            'overall_summary': {},
            'api_stats': {}
        }
        
        # Run tests for each agent and scenario
        for agent_id in range(num_agents):
            agent_results = []
            for scenario in scenarios:
                try:
                    logger.info(f"Testing agent_{agent_id:03d} on {scenario}")
                    result = self.test_single_spatial_reasoning(f"agent_{agent_id:03d}", scenario)
                    agent_results.append(result)
                    
                    # Add delay to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Test failed for agent {agent_id}, scenario {scenario}: {e}")
                    continue
            
            results['agent_results'].append({
                'agent_id': f'agent_{agent_id:03d}',
                'results': agent_results
            })
        
        # Calculate scenario summaries
        for scenario in scenarios:
            scenario_results = []
            for agent_data in results['agent_results']:
                for result in agent_data['results']:
                    if result['scenario'] == scenario:
                        scenario_results.append(result)
            
            if scenario_results:
                avg_efficiency = sum(r['path_efficiency'] for r in scenario_results) / len(scenario_results)
                avg_avoidance = sum(r['obstacle_avoidance_rate'] for r in scenario_results) / len(scenario_results)
                avg_completion = sum(r['task_completion_rate'] for r in scenario_results) / len(scenario_results)
                avg_understanding = sum(r['spatial_understanding_score'] for r in scenario_results) / len(scenario_results)
                
                results['scenario_summaries'][scenario] = {
                    'num_tests': len(scenario_results),
                    'avg_path_efficiency': avg_efficiency,
                    'avg_obstacle_avoidance_rate': avg_avoidance,
                    'avg_task_completion_rate': avg_completion,
                    'avg_spatial_understanding_score': avg_understanding
                }
        
        # Calculate overall summary
        all_results = []
        for agent_data in results['agent_results']:
            all_results.extend(agent_data['results'])
        
        if all_results:
            results['overall_summary'] = {
                'total_tests': len(all_results),
                'avg_path_efficiency': sum(r['path_efficiency'] for r in all_results) / len(all_results),
                'avg_obstacle_avoidance_rate': sum(r['obstacle_avoidance_rate'] for r in all_results) / len(all_results),
                'avg_task_completion_rate': sum(r['task_completion_rate'] for r in all_results) / len(all_results),
                'avg_spatial_understanding_score': sum(r['spatial_understanding_score'] for r in all_results) / len(all_results),
                'total_navigation_time': sum(r['total_response_time'] for r in all_results),
                'total_collisions': sum(r['collisions'] for r in all_results)
            }
        
        # Add API statistics
        results['api_stats'] = self.stats.copy()
        results['test_info']['end_time'] = datetime.now().isoformat()
        
        return results

def main():
    """Main function"""
    
    print("🧪 SIMPLE SPATIAL REASONING TEST")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not found. Please set environment variable.")
        print("💡 Get free API key from: https://console.groq.com/")
        return
    
    print(f"✅ API key configured: {api_key[:10]}...")
    
    # Initialize test runner
    runner = SimpleSpatialTestRunner()
    
    # Run comprehensive test
    print("\n🚀 Running comprehensive spatial reasoning test...")
    results = runner.run_comprehensive_test(num_agents=3)  # Start with 3 agents
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"simple_spatial_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Test completed!")
    print(f"📁 Results saved to: {filename}")
    
    # Print summary
    if results['overall_summary']:
        summary = results['overall_summary']
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Average path efficiency: {summary['avg_path_efficiency']:.3f}")
        print(f"   Average obstacle avoidance: {summary['avg_obstacle_avoidance_rate']:.3f}")
        print(f"   Average task completion: {summary['avg_task_completion_rate']:.3f}")
        print(f"   Average spatial understanding: {summary['avg_spatial_understanding_score']:.3f}")
        print(f"   Total navigation time: {summary['total_navigation_time']:.1f}s")
        print(f"   Total collisions: {summary['total_collisions']}")
    
    # Print scenario summaries
    print(f"\n📈 SCENARIO RESULTS:")
    for scenario, summary in results['scenario_summaries'].items():
        print(f"   {scenario}:")
        print(f"     Tests: {summary['num_tests']}")
        print(f"     Path efficiency: {summary['avg_path_efficiency']:.3f}")
        print(f"     Spatial understanding: {summary['avg_spatial_understanding_score']:.3f}")
    
    # Print API statistics
    api_stats = results['api_stats']
    print(f"\n🔌 API STATISTICS:")
    print(f"   Total requests: {api_stats['total_requests']}")
    print(f"   Successful: {api_stats['successful_requests']}")
    print(f"   Failed: {api_stats['failed_requests']}")
    print(f"   Total tokens: {api_stats['total_tokens']}")
    if api_stats['total_requests'] > 0:
        print(f"   Success rate: {api_stats['successful_requests']/api_stats['total_requests']*100:.1f}%")

if __name__ == "__main__":
    main()
