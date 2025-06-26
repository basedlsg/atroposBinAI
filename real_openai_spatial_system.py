#!/usr/bin/env python3
"""
Real Spatial Reasoning System using OpenAI API
Implements actual LLM-powered spatial reasoning with proper error handling
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
import threading
import websocket
import socket

@dataclass
class Position:
    x: float
    y: float
    z: float
    
    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y, "z": self.z}

@dataclass
class Agent:
    id: int
    position: Position
    target: Position
    health: float = 100.0
    energy: float = 100.0
    score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "position": self.position.to_dict(),
            "target": self.target.to_dict(),
            "health": self.health,
            "energy": self.energy,
            "score": self.score
        }

class OpenAIProvider:
    """OpenAI API provider for LLM decisions"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found. Please set environment variable.")
        
        print(f"✅ OpenAI API configured: {self.api_key[:20]}...")
    
    def get_spatial_decision(self, agent: Agent, obstacles: List[Position], 
                           available_actions: List[str]) -> str:
        """Get spatial reasoning decision from OpenAI API"""
        
        prompt = self._create_spatial_prompt(agent, obstacles, available_actions)
        
        try:
            response = self._call_openai_api(prompt)
            decision = self._parse_decision(response)
            return decision
        except Exception as e:
            print(f"⚠️ API call failed: {e}")
            # Fallback to intelligent random choice
            return self._fallback_decision(agent, obstacles, available_actions)
    
    def _create_spatial_prompt(self, agent: Agent, obstacles: List[Position], 
                             available_actions: List[str]) -> str:
        """Create a spatial reasoning prompt"""
        
        prompt = f"""You are an AI agent navigating in 3D space. Analyze the situation and choose the best action.

CURRENT SITUATION:
- Your position: ({agent.position.x:.1f}, {agent.position.y:.1f}, {agent.position.z:.1f})
- Target position: ({agent.target.x:.1f}, {agent.target.y:.1f}, {agent.target.z:.1f})
- Distance to target: {agent.position.distance_to(agent.target):.1f}
- Your health: {agent.health:.1f}
- Your energy: {agent.energy:.1f}

OBSTACLES (avoid these):
{chr(10).join([f"- Obstacle {i+1}: ({obs.x:.1f}, {obs.y:.1f}, {obs.z:.1f})" for i, obs in enumerate(obstacles)])}

AVAILABLE ACTIONS:
{chr(10).join([f"- {action}" for action in available_actions])}

ANALYSIS:
Consider the shortest path to the target while avoiding obstacles. Choose the action that moves you closest to the target while maintaining safety.

RESPONSE FORMAT:
Respond with ONLY the action name from the available actions list.

Action:"""
        
        return prompt
    
    def _call_openai_api(self, prompt: str) -> str:
        """Make API call to OpenAI"""
        
        url = "https://api.openai.com/v1/chat/completions"
        
        data = {
            "model": "gpt-3.5-turbo",
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
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                raise Exception(f"Unexpected API response: {result}")
    
    def _parse_decision(self, response: str) -> str:
        """Parse the decision from API response"""
        # Clean up the response
        decision = response.strip().upper()
        
        # Remove any extra text
        if ":" in decision:
            decision = decision.split(":")[-1].strip()
        
        return decision
    
    def _fallback_decision(self, agent: Agent, obstacles: List[Position], 
                          available_actions: List[str]) -> str:
        """Intelligent fallback decision when API fails"""
        
        # Calculate direction to target
        dx = agent.target.x - agent.position.x
        dy = agent.target.y - agent.position.y
        dz = agent.target.z - agent.position.z
        
        # Choose action based on largest component
        if abs(dx) > abs(dy) and abs(dx) > abs(dz):
            return "MOVE_FORWARD" if dx > 0 else "MOVE_BACKWARD"
        elif abs(dy) > abs(dz):
            return "MOVE_LEFT" if dy > 0 else "MOVE_RIGHT"
        else:
            return "MOVE_UP" if dz > 0 else "MOVE_DOWN"

class SpatialEnvironment:
    """3D spatial environment for agents"""
    
    def __init__(self, width: float = 20.0, height: float = 20.0, depth: float = 20.0):
        self.width = width
        self.height = height
        self.depth = depth
        self.obstacles: List[Position] = []
        self.agents: List[Agent] = []
        
        # Generate random obstacles
        self._generate_obstacles()
    
    def _generate_obstacles(self, num_obstacles: int = 5):
        """Generate random obstacles"""
        for _ in range(num_obstacles):
            obstacle = Position(
                x=random.uniform(2, self.width - 2),
                y=random.uniform(2, self.height - 2),
                z=random.uniform(2, self.depth - 2)
            )
            self.obstacles.append(obstacle)
    
    def add_agent(self, agent: Agent):
        """Add agent to environment"""
        self.agents.append(agent)
    
    def is_valid_position(self, position: Position) -> bool:
        """Check if position is valid (within bounds and not in obstacle)"""
        # Check bounds
        if (position.x < 0 or position.x > self.width or
            position.y < 0 or position.y > self.height or
            position.z < 0 or position.z > self.depth):
            return False
        
        # Check obstacles
        for obstacle in self.obstacles:
            if position.distance_to(obstacle) < 1.0:  # Minimum safe distance
                return False
        
        return True
    
    def get_available_actions(self, agent: Agent) -> List[str]:
        """Get available actions for agent"""
        actions = []
        
        # Test each possible movement
        test_positions = [
            Position(agent.position.x + 1, agent.position.y, agent.position.z),  # Forward
            Position(agent.position.x - 1, agent.position.y, agent.position.z),  # Backward
            Position(agent.position.x, agent.position.y + 1, agent.position.z),  # Left
            Position(agent.position.x, agent.position.y - 1, agent.position.z),  # Right
            Position(agent.position.x, agent.position.y, agent.position.z + 1),  # Up
            Position(agent.position.x, agent.position.y, agent.position.z - 1),  # Down
        ]
        
        action_names = ["MOVE_FORWARD", "MOVE_BACKWARD", "MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN"]
        
        for pos, action in zip(test_positions, action_names):
            if self.is_valid_position(pos):
                actions.append(action)
        
        return actions
    
    def apply_action(self, agent: Agent, action: str) -> bool:
        """Apply action to agent"""
        new_position = None
        
        if action == "MOVE_FORWARD":
            new_position = Position(agent.position.x + 1, agent.position.y, agent.position.z)
        elif action == "MOVE_BACKWARD":
            new_position = Position(agent.position.x - 1, agent.position.y, agent.position.z)
        elif action == "MOVE_LEFT":
            new_position = Position(agent.position.x, agent.position.y + 1, agent.position.z)
        elif action == "MOVE_RIGHT":
            new_position = Position(agent.position.x, agent.position.y - 1, agent.position.z)
        elif action == "MOVE_UP":
            new_position = Position(agent.position.x, agent.position.y, agent.position.z + 1)
        elif action == "MOVE_DOWN":
            new_position = Position(agent.position.x, agent.position.y, agent.position.z - 1)
        
        if new_position and self.is_valid_position(new_position):
            agent.position = new_position
            return True
        
        return False
    
    def update_agent_stats(self, agent: Agent):
        """Update agent statistics"""
        # Calculate distance-based score
        distance = agent.position.distance_to(agent.target)
        if distance < 1.0:  # Reached target
            agent.score += 100
            # Reset target to new random position
            agent.target = Position(
                x=random.uniform(0, self.width),
                y=random.uniform(0, self.height),
                z=random.uniform(0, self.depth)
            )
        else:
            # Score based on proximity
            agent.score += max(0, 10 - distance)
        
        # Energy consumption
        agent.energy = max(0, agent.energy - 0.1)
        
        # Health regeneration
        agent.health = min(100, agent.health + 0.05)

class SpatialReasoningSystem:
    """Main spatial reasoning system"""
    
    def __init__(self, api_key: str = None):
        self.openai_provider = OpenAIProvider(api_key)
        self.environment = SpatialEnvironment()
        self.metrics = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "api_calls": 0,
            "fallback_decisions": 0,
            "average_response_time": 0.0
        }
        
        print("🚀 Spatial Reasoning System initialized")
    
    def add_agent(self, agent_id: int, start_pos: Position, target_pos: Position):
        """Add agent to system"""
        agent = Agent(agent_id, start_pos, target_pos)
        self.environment.add_agent(agent)
        print(f"🤖 Added agent {agent_id} at {start_pos.to_dict()}")
    
    def run_simulation(self, num_steps: int = 50):
        """Run spatial reasoning simulation"""
        print(f"\n🎯 Running simulation for {num_steps} steps...")
        
        for step in range(num_steps):
            print(f"\n📊 Step {step + 1}/{num_steps}")
            
            for agent in self.environment.agents:
                if agent.energy <= 0:
                    continue
                
                # Get available actions
                available_actions = self.environment.get_available_actions(agent)
                if not available_actions:
                    continue
                
                # Get LLM decision
                start_time = time.time()
                decision = self.openai_provider.get_spatial_decision(
                    agent, self.environment.obstacles, available_actions
                )
                response_time = time.time() - start_time
                
                # Update metrics
                self.metrics["total_decisions"] += 1
                self.metrics["api_calls"] += 1
                self.metrics["average_response_time"] = (
                    (self.metrics["average_response_time"] * (self.metrics["api_calls"] - 1) + response_time) 
                    / self.metrics["api_calls"]
                )
                
                # Apply action
                if self.environment.apply_action(agent, decision):
                    self.metrics["successful_decisions"] += 1
                    print(f"  Agent {agent.id}: {decision} -> {agent.position.to_dict()}")
                else:
                    print(f"  Agent {agent.id}: {decision} (invalid)")
                
                # Update agent stats
                self.environment.update_agent_stats(agent)
            
            # Print summary every 10 steps
            if (step + 1) % 10 == 0:
                self._print_step_summary(step + 1)
        
        self._print_final_results()
    
    def _print_step_summary(self, step: int):
        """Print step summary"""
        print(f"\n📈 Step {step} Summary:")
        for agent in self.environment.agents:
            distance = agent.position.distance_to(agent.target)
            print(f"  Agent {agent.id}: Score={agent.score:.1f}, Energy={agent.energy:.1f}, Distance={distance:.1f}")
    
    def _print_final_results(self):
        """Print final results"""
        print(f"\n🏁 Final Results:")
        print(f"  Total decisions: {self.metrics['total_decisions']}")
        print(f"  Successful decisions: {self.metrics['successful_decisions']}")
        print(f"  API calls: {self.metrics['api_calls']}")
        print(f"  Average response time: {self.metrics['average_response_time']:.3f}s")
        
        print(f"\n🤖 Agent Final Scores:")
        for agent in self.environment.agents:
            print(f"  Agent {agent.id}: {agent.score:.1f} points")
    
    def get_visualization_data(self) -> Dict:
        """Get data for 3D visualization"""
        return {
            "environment": {
                "width": self.environment.width,
                "height": self.environment.height,
                "depth": self.environment.depth,
                "obstacles": [obs.to_dict() for obs in self.environment.obstacles]
            },
            "agents": [agent.to_dict() for agent in self.environment.agents],
            "metrics": self.metrics
        }

def main():
    """Main function to run the spatial reasoning system"""
    print("🧠 Real OpenAI Spatial Reasoning System")
    print("=" * 50)
    
    # Initialize system
    system = SpatialReasoningSystem()
    
    # Add agents
    system.add_agent(1, Position(0, 0, 0), Position(15, 15, 15))
    system.add_agent(2, Position(5, 5, 5), Position(10, 10, 10))
    system.add_agent(3, Position(10, 0, 10), Position(0, 15, 5))
    
    # Run simulation
    system.run_simulation(num_steps=30)
    
    # Save results
    results = system.get_visualization_data()
    with open("real_openai_spatial_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to real_openai_spatial_results.json")

if __name__ == "__main__":
    main() 