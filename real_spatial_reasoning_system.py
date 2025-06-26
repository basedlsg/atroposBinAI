#!/usr/bin/env python3
"""
Real Spatial Reasoning System
Integrates with existing Groq API and 3D visualization infrastructure
"""

import asyncio
import json
import time
import logging
import os
import requests
import websockets
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SpatialObject:
    """Real 3D object in spatial environment"""
    id: str
    position: Tuple[float, float, float]
    object_type: str  # "agent", "target", "obstacle", "resource"
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    properties: Dict = None

@dataclass
class AgentDecision:
    """Real agent decision from LLM"""
    action: str
    reasoning: str
    confidence: float
    response_time: float
    tokens_used: int

class RealSpatialReasoningSystem:
    """Real spatial reasoning system with actual LLM integration"""
    
    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        self.base_url = 'https://api.groq.com/openai/v1/chat/completions'
        self.websocket_server = None
        self.visualization_clients = []
        self.agents = {}
        self.environment_objects = {}
        self.test_results = []
        
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found. Please set environment variable.")
    
    async def create_spatial_environment(self, scenario: str) -> Dict:
        """Create real 3D environment for testing"""
        
        environments = {
            "simple_navigation": {
                "dimensions": (20.0, 20.0, 10.0),
                "objects": [
                    {"id": "start", "position": (0, 0, 0), "type": "start", "color": (0, 1, 0, 1)},
                    {"id": "target", "position": (10, 10, 0), "type": "target", "color": (1, 0, 0, 1)}
                ],
                "obstacles": [],
                "description": "Navigate from start to target without obstacles"
            },
            "obstacle_avoidance": {
                "dimensions": (20.0, 20.0, 10.0),
                "objects": [
                    {"id": "start", "position": (0, 0, 0), "type": "start", "color": (0, 1, 0, 1)},
                    {"id": "target", "position": (15, 15, 0), "type": "target", "color": (1, 0, 0, 1)}
                ],
                "obstacles": [
                    {"id": "obstacle_1", "position": (5, 5, 0), "type": "obstacle", "color": (0.5, 0.5, 0.5, 1), "scale": (2, 2, 2)},
                    {"id": "obstacle_2", "position": (10, 8, 0), "type": "obstacle", "color": (0.5, 0.5, 0.5, 1), "scale": (1.5, 1.5, 1.5)},
                    {"id": "obstacle_3", "position": (8, 12, 0), "type": "obstacle", "color": (0.5, 0.5, 0.5, 1), "scale": (2, 2, 2)}
                ],
                "description": "Navigate around static obstacles to reach target"
            },
            "spatial_memory": {
                "dimensions": (20.0, 20.0, 10.0),
                "objects": [
                    {"id": "start", "position": (0, 0, 0), "type": "start", "color": (0, 1, 0, 1)},
                    {"id": "resource_1", "position": (8, 6, 0), "type": "resource", "color": (0, 0, 1, 1)},
                    {"id": "resource_2", "position": (12, 4, 0), "type": "resource", "color": (0, 0, 1, 1)},
                    {"id": "target", "position": (15, 15, 0), "type": "target", "color": (1, 0, 0, 1)}
                ],
                "obstacles": [],
                "description": "Remember and navigate to previously seen resource location"
            }
        }
        
        return environments.get(scenario, environments["simple_navigation"])
    
    async def get_llm_spatial_decision(self, agent_id: str, environment: Dict, 
                                     current_pos: List[float], target_pos: Tuple[float, float, float],
                                     scenario: str) -> AgentDecision:
        """Get real LLM decision for spatial reasoning"""
        
        # Create comprehensive spatial reasoning prompt
        prompt = self._create_spatial_reasoning_prompt(
            agent_id, environment, current_pos, target_pos, scenario
        )
        
        headers = {
            'Authorization': f'Bearer {self.groq_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'llama-3.1-8b-instant',
            'messages': [
                {'role': 'system', 'content': 'You are an AI agent navigating in a 3D environment. Respond with valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 200,
            'temperature': 0.7
        }
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0]['message']['content'].strip()
                            tokens_used = data.get('usage', {}).get('total_tokens', 0)
                            
                            # Parse JSON response
                            try:
                                decision_data = json.loads(content)
                                return AgentDecision(
                                    action=decision_data.get('action', 'rest'),
                                    reasoning=decision_data.get('reasoning', 'No reasoning provided'),
                                    confidence=decision_data.get('confidence', 0.5),
                                    response_time=response_time,
                                    tokens_used=tokens_used
                                )
                            except json.JSONDecodeError:
                                # Fallback parsing
                                return AgentDecision(
                                    action=self._extract_action_from_text(content),
                                    reasoning=content[:100],
                                    confidence=0.5,
                                    response_time=response_time,
                                    tokens_used=tokens_used
                                )
                        else:
                            return AgentDecision(
                                action='rest',
                                reasoning='No response generated',
                                confidence=0.0,
                                response_time=response_time,
                                tokens_used=0
                            )
                    else:
                        error_text = await response.text()
                        return AgentDecision(
                            action='rest',
                            reasoning=f'API Error: {response.status} - {error_text}',
                            confidence=0.0,
                            response_time=response_time,
                            tokens_used=0
                        )
                        
        except Exception as e:
            return AgentDecision(
                action='rest',
                reasoning=f'Request failed: {str(e)}',
                confidence=0.0,
                response_time=time.time() - start_time,
                tokens_used=0
            )
    
    def _create_spatial_reasoning_prompt(self, agent_id: str, environment: Dict,
                                       current_pos: List[float], target_pos: Tuple[float, float, float],
                                       scenario: str) -> str:
        """Create comprehensive spatial reasoning prompt"""
        
        prompt = f"""You are Agent {agent_id} navigating in a 3D environment.

CURRENT SITUATION:
- Your position: {current_pos}
- Target position: {target_pos}
- Distance to target: {np.linalg.norm(np.array(target_pos) - np.array(current_pos)):.2f} units
- Scenario: {scenario}

ENVIRONMENT OBJECTS:"""

        # Add static objects
        for obj in environment.get('objects', []):
            if obj['type'] != 'start':
                distance = np.linalg.norm(np.array(obj['position']) - np.array(current_pos))
                prompt += f"\n- {obj['type']}: {obj['position']} (distance: {distance:.2f})"
        
        # Add obstacles
        for obstacle in environment.get('obstacles', []):
            distance = np.linalg.norm(np.array(obstacle['position']) - np.array(current_pos))
            prompt += f"\n- obstacle: {obstacle['position']} (distance: {distance:.2f})"
        
        prompt += f"""

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
1. Analyze the spatial relationships between your position and the target
2. Consider obstacles and find the best path
3. Choose the most efficient action to move toward the target
4. Avoid collisions with obstacles
5. Respond with valid JSON only

Respond with JSON: {{"action": "move_direction", "reasoning": "brief explanation", "confidence": 0.0-1.0}}"""

        return prompt
    
    def _extract_action_from_text(self, text: str) -> str:
        """Extract action from text response if JSON parsing fails"""
        
        text_upper = text.upper()
        actions = ['move_north', 'move_south', 'move_east', 'move_west', 
                  'move_northeast', 'move_northwest', 'move_southeast', 'move_southwest']
        
        for action in actions:
            if action.upper() in text_upper:
                return action
        
        return 'rest'
    
    def _calculate_next_position(self, current_pos: List[float], action: str) -> List[float]:
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
    
    def _check_collision(self, position: List[float], obstacles: List[Dict]) -> bool:
        """Check if position collides with any obstacles"""
        
        for obstacle in obstacles:
            distance = np.linalg.norm(np.array(position) - np.array(obstacle['position']))
            collision_radius = obstacle.get('scale', [1, 1, 1])[0]
            if distance < collision_radius:
                return True
        return False
    
    async def run_spatial_reasoning_test(self, agent_id: str, scenario: str, 
                                       max_steps: int = 50) -> Dict:
        """Run real spatial reasoning test with actual LLM"""
        
        logger.info(f"Running spatial reasoning test for agent {agent_id} on scenario {scenario}")
        
        # Create environment
        environment = await self.create_spatial_environment(scenario)
        
        # Initialize agent position
        start_pos = environment['objects'][0]['position']  # Start position
        target_pos = None
        
        # Find target position
        for obj in environment['objects']:
            if obj['type'] == 'target':
                target_pos = obj['position']
                break
        
        if not target_pos:
            raise ValueError(f"No target found in scenario {scenario}")
        
        # Calculate optimal path length
        optimal_path_length = np.linalg.norm(np.array(target_pos) - np.array(start_pos))
        
        # Run navigation simulation
        current_position = list(start_pos)
        path_taken = [current_position.copy()]
        collisions = 0
        navigation_time = 0.0
        decisions = []
        
        for step in range(max_steps):
            # Get LLM decision
            decision = await self.get_llm_spatial_decision(
                agent_id, environment, current_position, target_pos, scenario
            )
            
            decisions.append(decision)
            navigation_time += decision.response_time
            
            # Calculate next position
            next_position = self._calculate_next_position(current_position, decision.action)
            
            # Check for collisions
            if self._check_collision(next_position, environment.get('obstacles', [])):
                collisions += 1
                # Try alternative path
                next_position = self._calculate_alternative_path(
                    current_position, target_pos, environment.get('obstacles', [])
                )
            
            # Update position
            current_position = next_position
            path_taken.append(current_position.copy())
            
            # Check if target reached
            distance_to_target = np.linalg.norm(
                np.array(current_position) - np.array(target_pos)
            )
            
            if distance_to_target < 1.0:  # Target reached
                break
        
        # Calculate metrics
        actual_path_length = self._calculate_path_length(path_taken)
        path_efficiency = optimal_path_length / actual_path_length if actual_path_length > 0 else 0
        
        total_obstacles = len(environment.get('obstacles', []))
        successful_avoidances = total_obstacles - collisions
        obstacle_avoidance_rate = successful_avoidances / total_obstacles if total_obstacles > 0 else 1.0
        
        task_completion_rate = 1.0 if distance_to_target < 1.0 else 0.0
        
        # Calculate spatial understanding score
        spatial_understanding_score = (
            path_efficiency * 0.3 +
            obstacle_avoidance_rate * 0.25 +
            (1.0 - collisions / max(1, len(path_taken))) * 0.2 +
            task_completion_rate * 0.15 +
            (1.0 - navigation_time / 60.0) * 0.1  # Normalize time
        )
        
        result = {
            "agent_id": agent_id,
            "scenario": scenario,
            "path_taken": path_taken,
            "final_position": current_position,
            "target_reached": distance_to_target < 1.0,
            "navigation_time": navigation_time,
            "collisions": collisions,
            "total_steps": len(path_taken),
            "path_efficiency": path_efficiency,
            "obstacle_avoidance_rate": obstacle_avoidance_rate,
            "task_completion_rate": task_completion_rate,
            "spatial_understanding_score": spatial_understanding_score,
            "decisions": [
                {
                    "action": d.action,
                    "reasoning": d.reasoning,
                    "confidence": d.confidence,
                    "response_time": d.response_time,
                    "tokens_used": d.tokens_used
                } for d in decisions
            ]
        }
        
        self.test_results.append(result)
        return result
    
    def _calculate_alternative_path(self, current_pos: List[float], target_pos: Tuple[float, float, float],
                                  obstacles: List[Dict]) -> List[float]:
        """Calculate alternative path when collision detected"""
        
        for obstacle in obstacles:
            distance = np.linalg.norm(np.array(current_pos) - np.array(obstacle['position']))
            collision_radius = obstacle.get('scale', [1, 1, 1])[0]
            if distance < collision_radius + 1.0:
                # Move away from obstacle
                direction = np.array(current_pos) - np.array(obstacle['position'])
                direction = direction / np.linalg.norm(direction)
                next_pos = np.array(current_pos) + direction
                return next_pos.tolist()
        
        return current_pos
    
    def _calculate_path_length(self, path: List[List[float]]) -> float:
        """Calculate total path length"""
        
        total_length = 0.0
        for i in range(1, len(path)):
            segment_length = np.linalg.norm(np.array(path[i]) - np.array(path[i-1]))
            total_length += segment_length
        
        return total_length
    
    async def run_comprehensive_test_suite(self, num_agents: int = 10) -> Dict:
        """Run comprehensive test suite with multiple agents and scenarios"""
        
        logger.info(f"Running comprehensive test suite with {num_agents} agents")
        
        scenarios = ["simple_navigation", "obstacle_avoidance", "spatial_memory"]
        results = {
            "test_suite": {
                "num_agents": num_agents,
                "scenarios": scenarios,
                "start_time": datetime.now().isoformat(),
                "total_tests": num_agents * len(scenarios)
            },
            "agent_results": [],
            "scenario_summaries": {},
            "overall_summary": {}
        }
        
        # Run tests for each agent and scenario
        for agent_id in range(num_agents):
            agent_results = []
            for scenario in scenarios:
                try:
                    result = await self.run_spatial_reasoning_test(
                        f"agent_{agent_id:03d}", scenario
                    )
                    agent_results.append(result)
                    
                    # Add delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Test failed for agent {agent_id}, scenario {scenario}: {e}")
                    continue
            
            results["agent_results"].append({
                "agent_id": f"agent_{agent_id:03d}",
                "results": agent_results
            })
        
        # Calculate scenario summaries
        for scenario in scenarios:
            scenario_results = []
            for agent_data in results["agent_results"]:
                for result in agent_data["results"]:
                    if result["scenario"] == scenario:
                        scenario_results.append(result)
            
            if scenario_results:
                avg_efficiency = np.mean([r["path_efficiency"] for r in scenario_results])
                avg_avoidance = np.mean([r["obstacle_avoidance_rate"] for r in scenario_results])
                avg_completion = np.mean([r["task_completion_rate"] for r in scenario_results])
                avg_understanding = np.mean([r["spatial_understanding_score"] for r in scenario_results])
                
                results["scenario_summaries"][scenario] = {
                    "num_tests": len(scenario_results),
                    "avg_path_efficiency": avg_efficiency,
                    "avg_obstacle_avoidance_rate": avg_avoidance,
                    "avg_task_completion_rate": avg_completion,
                    "avg_spatial_understanding_score": avg_understanding
                }
        
        # Calculate overall summary
        all_results = []
        for agent_data in results["agent_results"]:
            all_results.extend(agent_data["results"])
        
        if all_results:
            results["overall_summary"] = {
                "total_tests": len(all_results),
                "avg_path_efficiency": np.mean([r["path_efficiency"] for r in all_results]),
                "avg_obstacle_avoidance_rate": np.mean([r["obstacle_avoidance_rate"] for r in all_results]),
                "avg_task_completion_rate": np.mean([r["task_completion_rate"] for r in all_results]),
                "avg_spatial_understanding_score": np.mean([r["spatial_understanding_score"] for r in all_results]),
                "total_navigation_time": sum([r["navigation_time"] for r in all_results]),
                "total_collisions": sum([r["collisions"] for r in all_results])
            }
        
        results["test_suite"]["end_time"] = datetime.now().isoformat()
        
        return results
    
    async def start_websocket_server(self, port: int = 8765):
        """Start WebSocket server for 3D visualization"""
        
        async def websocket_handler(websocket, path):
            self.visualization_clients.append(websocket)
            try:
                async for message in websocket:
                    # Handle client messages if needed
                    pass
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.visualization_clients.remove(websocket)
        
        self.websocket_server = await websockets.serve(websocket_handler, "localhost", port)
        logger.info(f"WebSocket server started on port {port}")
    
    async def send_visualization_update(self, environment: Dict, agent_positions: Dict[str, List[float]]):
        """Send visualization update to connected clients"""
        
        if not self.visualization_clients:
            return
        
        # Prepare scene data for Three.js
        scene_data = {
            "type": "scene_update",
            "payload": []
        }
        
        # Add environment objects
        for obj in environment.get('objects', []):
            scene_data["payload"].append({
                "id": obj['id'],
                "position": obj['position'],
                "type": "cube" if obj['type'] in ['start', 'target'] else "sphere",
                "color_rgba": obj['color'],
                "scale": obj.get('scale', [1, 1, 1])
            })
        
        # Add obstacles
        for obstacle in environment.get('obstacles', []):
            scene_data["payload"].append({
                "id": obstacle['id'],
                "position": obstacle['position'],
                "type": "cube",
                "color_rgba": obstacle['color'],
                "scale": obstacle['scale']
            })
        
        # Add agents
        for agent_id, position in agent_positions.items():
            scene_data["payload"].append({
                "id": agent_id,
                "position": position,
                "type": "sphere",
                "color_rgba": (0, 0, 1, 1),  # Blue for agents
                "scale": [0.5, 0.5, 0.5]
            })
        
        # Send to all connected clients
        message = json.dumps(scene_data)
        for client in self.visualization_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                continue

async def main():
    """Main function to run real spatial reasoning tests"""
    
    print("🧪 REAL SPATIAL REASONING SYSTEM")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not found. Please set environment variable.")
        return
    
    print(f"✅ API key configured: {api_key[:10]}...")
    
    # Initialize system
    system = RealSpatialReasoningSystem(api_key)
    
    # Start WebSocket server for visualization
    await system.start_websocket_server()
    
    # Run comprehensive test suite
    print("\n🚀 Running comprehensive test suite...")
    results = await system.run_comprehensive_test_suite(num_agents=5)  # Start with 5 agents
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"real_spatial_reasoning_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Test suite completed!")
    print(f"📁 Results saved to: {filename}")
    
    # Print summary
    if results["overall_summary"]:
        summary = results["overall_summary"]
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
    for scenario, summary in results["scenario_summaries"].items():
        print(f"   {scenario}:")
        print(f"     Tests: {summary['num_tests']}")
        print(f"   Path efficiency: {summary['avg_path_efficiency']:.3f}")
        print(f"   Spatial understanding: {summary['avg_spatial_understanding_score']:.3f}")
    
    print(f"\n🌐 WebSocket server running on ws://localhost:8765")
    print(f"📱 Open visualization/index.html to view 3D visualization")
    
    # Keep server running for visualization
    try:
        await asyncio.Future()  # Run indefinitely
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
