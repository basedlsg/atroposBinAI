#!/usr/bin/env python3
"""
Ultimate Society Demo - Showcasing the best of our enhanced LLM society simulation
Features: Advanced agent communication, real-time analytics, economic systems, and more
"""

import json
import time
import random
import asyncio
from datetime import datetime
from dataclasses import asdict
from typing import List, Dict, Any
import logging

# Import our enhanced systems
from integrated_enhanced_society import EnhancedSocietySimulator, EnhancedAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateSocietyDemo:
    """Ultimate demonstration of our enhanced LLM society simulation"""
    
    def __init__(self, num_agents: int = 100):
        self.num_agents = num_agents
        self.simulator = None
        self.demo_results = []
        
        # Demo configuration
        self.demo_phases = [
            {"name": "Initialization", "steps": 10, "description": "Agents spawn and establish initial positions"},
            {"name": "Early Interactions", "steps": 20, "description": "First communications and basic trading"},
            {"name": "Community Formation", "steps": 30, "description": "Social groups and alliances form"},
            {"name": "Economic Development", "steps": 25, "description": "Complex trading networks emerge"},
            {"name": "Mature Society", "steps": 35, "description": "Sophisticated cooperation and competition"},
        ]
        
    async def run_ultimate_demo(self):
        """Run the ultimate society simulation demo"""
        print("🚀 ULTIMATE LLM SOCIETY SIMULATION DEMO")
        print("=" * 60)
        print(f"Initializing simulation with {self.num_agents} agents...")
        print("Features: Enhanced Communication, LLM Decision Making, Economic Systems")
        print()
        
        # Initialize simulation
        self.simulator = EnhancedSocietySimulator(num_agents=self.num_agents)
        
        # Print initial state
        self.print_initial_state()
        
        # Run the complete simulation
        print(f"\n🎬 STARTING SIMULATION")
        print("-" * 50)
        
        total_steps = sum(phase['steps'] for phase in self.demo_phases)
        start_time = time.time()
        
        # Run simulation
        await self.simulator.run_simulation(steps=total_steps)
        
        duration = time.time() - start_time
        
        # Final analysis
        print(f"\n🎯 SIMULATION COMPLETE")
        print(f"Total Steps: {total_steps}")
        print(f"Duration: {duration:.1f} seconds")
        print("=" * 60)
        
        self.print_final_analysis()
        self.export_demo_results()
        
    def print_initial_state(self):
        """Print initial simulation state"""
        agents = self.simulator.agents
        
        print(f"👥 INITIAL AGENT POPULATION: {len(agents)}")
        
        # Personality distribution
        personality_counts = {}
        for agent in agents:
            for trait, value in agent.personality.items():
                if trait not in personality_counts:
                    personality_counts[trait] = []
                personality_counts[trait].append(value)
        
        print("\n🧠 PERSONALITY DISTRIBUTION:")
        for trait, values in personality_counts.items():
            avg_value = sum(values) / len(values)
            print(f"  {trait.capitalize()}: {avg_value:.3f} (avg)")
            
        # Initial economic state
        total_wealth = sum(agent.wealth for agent in agents)
        avg_wealth = total_wealth / len(agents)
        print(f"\n💰 INITIAL ECONOMIC STATE:")
        print(f"  Total Wealth: ${total_wealth:.2f}")
        print(f"  Average Wealth: ${avg_wealth:.2f}")
        
        # Initial health and happiness
        avg_health = sum(agent.health for agent in agents) / len(agents)
        avg_happiness = sum(agent.happiness for agent in agents) / len(agents)
        print(f"\n❤️  INITIAL WELLBEING:")
        print(f"  Average Health: {avg_health:.3f}")
        print(f"  Average Happiness: {avg_happiness:.3f}")
        
    def print_final_analysis(self):
        """Print comprehensive final analysis"""
        agents = self.simulator.agents
        metrics = self.simulator.metrics
        
        print("\n🔍 COMPREHENSIVE FINAL ANALYSIS")
        print("=" * 60)
        
        # Population analysis
        active_agents = sum(1 for agent in agents if agent.health > 0.1)
        print(f"👥 POPULATION ANALYSIS:")
        print(f"  Total Agents: {len(agents)}")
        print(f"  Active Agents: {active_agents} ({active_agents/len(agents)*100:.1f}%)")
        print(f"  Total Actions Taken: {sum(agent.actions_taken for agent in agents)}")
        
        # Economic analysis
        wealth_values = [agent.wealth for agent in agents]
        wealth_values.sort()
        median_wealth = wealth_values[len(wealth_values)//2] if wealth_values else 0
        total_wealth = sum(wealth_values)
        
        if len(wealth_values) > 10:
            top_10_percent = wealth_values[int(len(wealth_values)*0.9):]
            bottom_10_percent = wealth_values[:int(len(wealth_values)*0.1)]
            wealth_inequality = self.calculate_gini(wealth_values)
        else:
            top_10_percent = wealth_values[-1:] if wealth_values else [0]
            bottom_10_percent = wealth_values[:1] if wealth_values else [0]
            wealth_inequality = 0.0
        
        print(f"\n💰 ECONOMIC ANALYSIS:")
        print(f"  Total Wealth: ${total_wealth:.2f}")
        print(f"  Average Wealth: ${total_wealth/len(agents):.2f}")
        print(f"  Median Wealth: ${median_wealth:.2f}")
        print(f"  Wealth Inequality (Gini): {wealth_inequality:.3f}")
        print(f"  Top 10% Avg Wealth: ${sum(top_10_percent)/len(top_10_percent):.2f}")
        print(f"  Bottom 10% Avg Wealth: ${sum(bottom_10_percent)/len(bottom_10_percent):.2f}")
        
        # Social analysis
        total_messages = sum(agent.messages_sent for agent in agents)
        total_connections = sum(agent.social_connections for agent in agents)
        avg_happiness = sum(agent.happiness for agent in agents) / len(agents)
        avg_health = sum(agent.health for agent in agents) / len(agents)
        
        print(f"\n🤝 SOCIAL ANALYSIS:")
        print(f"  Total Messages Sent: {total_messages}")
        print(f"  Total Social Connections: {total_connections}")
        print(f"  Average Happiness: {avg_happiness:.3f}")
        print(f"  Average Health: {avg_health:.3f}")
        
        # Communication analysis
        print(f"\n💬 COMMUNICATION ANALYSIS:")
        print(f"  Messages per Agent: {total_messages/len(agents):.1f}")
        print(f"  Social Connections per Agent: {total_connections/len(agents):.1f}")
        
        # Performance metrics from simulator
        if hasattr(self.simulator, 'metrics') and self.simulator.metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for key, value in self.simulator.metrics.items():
                if isinstance(value, (int, float)):
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Personality analysis
        personality_analysis = self.analyze_personality_outcomes()
        print(f"\n🧠 PERSONALITY OUTCOMES:")
        for trait, data in personality_analysis.items():
            print(f"  {trait.capitalize()}: {data['correlation']:.3f} correlation with success")
            
    def calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient for inequality measurement"""
        if not values or len(values) < 2:
            return 0.0
            
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = [0]
        for val in sorted_values:
            cumsum.append(cumsum[-1] + val)
        
        if cumsum[-1] == 0:
            return 0.0
            
        return (n + 1 - 2 * sum(cumsum) / cumsum[-1]) / n
            
    def analyze_personality_outcomes(self) -> Dict[str, Dict[str, float]]:
        """Analyze correlation between personality traits and outcomes"""
        agents = self.simulator.agents
        
        # Calculate success metric (combination of wealth, happiness, health)
        for agent in agents:
            agent.success_score = (
                agent.wealth * 0.4 + 
                agent.happiness * 0.3 + 
                agent.health * 0.3
            )
            
        personality_analysis = {}
        
        # Get all personality traits
        trait_names = set()
        for agent in agents:
            trait_names.update(agent.personality.keys())
        
        for trait in trait_names:
            trait_values = []
            success_values = []
            
            for agent in agents:
                trait_value = agent.personality.get(trait, 0.5)
                trait_values.append(trait_value)
                success_values.append(agent.success_score)
                
            # Calculate correlation
            correlation = self.calculate_correlation(trait_values, success_values)
            
            personality_analysis[trait] = {
                'correlation': correlation,
                'avg_trait_value': sum(trait_values) / len(trait_values)
            }
            
        return personality_analysis
        
    def calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
            
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x_sq = sum(x[i] ** 2 for i in range(n))
        sum_y_sq = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x_sq - sum_x ** 2) * (n * sum_y_sq - sum_y ** 2)) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
        
    def export_demo_results(self):
        """Export demo results to JSON file"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'num_agents': self.num_agents,
            'final_metrics': getattr(self.simulator, 'metrics', {}),
            'agent_data': [
                {
                    'id': agent.agent_id,
                    'position': agent.position,
                    'health': agent.health,
                    'energy': agent.energy,
                    'happiness': agent.happiness,
                    'wealth': agent.wealth,
                    'personality': agent.personality,
                    'social_connections': agent.social_connections,
                    'actions_taken': agent.actions_taken,
                    'messages_sent': agent.messages_sent,
                    'success_score': getattr(agent, 'success_score', 0)
                }
                for agent in self.simulator.agents
            ]
        }
        
        filename = f"ultimate_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
            
        print(f"\n💾 RESULTS EXPORTED: {filename}")
        print(f"   File size: {len(json.dumps(export_data, default=str))} characters")
        
    async def run_interactive_demo(self):
        """Run an interactive version of the demo"""
        print("🎮 INTERACTIVE DEMO MODE")
        print("Commands: 'step', 'status', 'agents', 'export', 'quit'")
        print()
        
        self.simulator = EnhancedSocietySimulator(num_agents=20)  # Smaller for interactive
        
        while True:
            try:
                command = input("demo> ").strip().lower()
                
                if command == 'step':
                    await self.simulator.run_simulation(steps=1)
                    print(f"Simulation step completed")
                          
                elif command == 'status':
                    agents = self.simulator.agents
                    active_agents = sum(1 for agent in agents if agent.health > 0.1)
                    total_wealth = sum(agent.wealth for agent in agents)
                    avg_happiness = sum(agent.happiness for agent in agents) / len(agents)
                    total_messages = sum(agent.messages_sent for agent in agents)
                    
                    print(f"Simulation Status:")
                    print(f"  Active Agents: {active_agents}/{len(agents)}")
                    print(f"  Total Wealth: ${total_wealth:.2f}")
                    print(f"  Average Happiness: {avg_happiness:.3f}")
                    print(f"  Total Messages: {total_messages}")
                    
                elif command == 'agents':
                    for i, agent in enumerate(self.simulator.agents[:5]):  # Show first 5
                        print(f"  Agent {agent.agent_id}: "
                              f"pos=({agent.position['x']:.1f},{agent.position['y']:.1f}), "
                              f"wealth=${agent.wealth:.1f}, "
                              f"happiness={agent.happiness:.2f}")
                    if len(self.simulator.agents) > 5:
                        print(f"  ... and {len(self.simulator.agents) - 5} more agents")
                        
                elif command == 'export':
                    self.export_demo_results()
                    
                elif command == 'quit':
                    print("Demo ended.")
                    break
                    
                else:
                    print("Unknown command. Available: step, status, agents, export, quit")
                    
            except KeyboardInterrupt:
                print("\nDemo interrupted.")
                break
            except Exception as e:
                print(f"Error: {e}")

async def main():
    """Main demo function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        demo = UltimateSocietyDemo(num_agents=20)
        await demo.run_interactive_demo()
    else:
        demo = UltimateSocietyDemo(num_agents=100)
        await demo.run_ultimate_demo()

if __name__ == "__main__":
    asyncio.run(main())