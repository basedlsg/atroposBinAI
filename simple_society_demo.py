#!/usr/bin/env python3
"""
Simple Society Demo - Working demonstration of our enhanced LLM society simulation
Features: LLM decision making, agent interactions, economic systems
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

# Import our enhanced system
from integrated_enhanced_society import EnhancedSocietySimulator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleSocietyDemo:
    """Simple demonstration of our enhanced LLM society simulation"""
    
    def __init__(self, num_agents: int = 50):
        self.num_agents = num_agents
        self.simulator = None
        
    async def run_demo(self):
        """Run the society simulation demo"""
        print("🚀 ENHANCED LLM SOCIETY SIMULATION DEMO")
        print("=" * 60)
        print(f"Initializing simulation with {self.num_agents} agents...")
        print("Features: LLM Decision Making, Agent Communication, Economic Systems")
        print()
        
        # Initialize simulation
        self.simulator = EnhancedSocietySimulator(num_agents=self.num_agents)
        
        # Print initial state
        self.print_initial_state()
        
        # Run simulation
        print(f"\n🎬 STARTING SIMULATION")
        print("-" * 50)
        
        steps = 50  # Reasonable number for demo
        start_time = time.time()
        
        # Run simulation
        final_report = await self.simulator.run_simulation(steps=steps)
        
        duration = time.time() - start_time
        
        # Print results
        print(f"\n🎯 SIMULATION COMPLETE")
        print(f"Steps: {steps}")
        print(f"Duration: {duration:.1f} seconds")
        print("=" * 60)
        
        self.print_final_analysis(final_report)
        self.export_results(final_report)
        
    def print_initial_state(self):
        """Print initial simulation state"""
        agents = list(self.simulator.agents.values())
        
        print(f"👥 AGENT POPULATION: {len(agents)}")
        
        # Personality distribution
        personality_traits = {}
        for agent in agents:
            for trait, value in agent.personality.items():
                if trait not in personality_traits:
                    personality_traits[trait] = []
                personality_traits[trait].append(value)
        
        print("\n🧠 PERSONALITY DISTRIBUTION:")
        for trait, values in personality_traits.items():
            avg_value = sum(values) / len(values)
            print(f"  {trait.capitalize()}: {avg_value:.3f} (average)")
            
        # Initial economic state
        total_wealth = sum(agent.wealth for agent in agents)
        avg_wealth = total_wealth / len(agents)
        print(f"\n💰 INITIAL ECONOMIC STATE:")
        print(f"  Total Wealth: ${total_wealth:.2f}")
        print(f"  Average Wealth: ${avg_wealth:.2f}")
        
        # Initial wellbeing
        avg_health = sum(agent.health for agent in agents) / len(agents)
        avg_happiness = sum(agent.happiness for agent in agents) / len(agents)
        avg_energy = sum(agent.energy for agent in agents) / len(agents)
        print(f"\n❤️  INITIAL WELLBEING:")
        print(f"  Average Health: {avg_health:.1f}%")
        print(f"  Average Happiness: {avg_happiness:.1f}%")
        print(f"  Average Energy: {avg_energy:.1f}%")
        
    def print_final_analysis(self, final_report: Dict[str, Any]):
        """Print comprehensive final analysis"""
        agents = list(self.simulator.agents.values())
        
        print("\n🔍 FINAL ANALYSIS")
        print("=" * 50)
        
        # Population analysis
        active_agents = sum(1 for agent in agents if agent.health > 10)
        total_actions = sum(agent.actions_taken for agent in agents)
        
        print(f"👥 POPULATION:")
        print(f"  Total Agents: {len(agents)}")
        print(f"  Active Agents: {active_agents} ({active_agents/len(agents)*100:.1f}%)")
        print(f"  Total Actions: {total_actions}")
        print(f"  Actions per Agent: {total_actions/len(agents):.1f}")
        
        # Economic analysis
        wealth_values = [agent.wealth for agent in agents]
        wealth_values.sort()
        total_wealth = sum(wealth_values)
        median_wealth = wealth_values[len(wealth_values)//2] if wealth_values else 0
        
        print(f"\n💰 ECONOMIC ANALYSIS:")
        print(f"  Total Wealth: ${total_wealth:.2f}")
        print(f"  Average Wealth: ${total_wealth/len(agents):.2f}")
        print(f"  Median Wealth: ${median_wealth:.2f}")
        print(f"  Richest Agent: ${max(wealth_values):.2f}")
        print(f"  Poorest Agent: ${min(wealth_values):.2f}")
        
        # Social analysis
        total_messages = sum(agent.messages_sent for agent in agents)
        total_connections = sum(agent.social_connections for agent in agents)
        avg_happiness = sum(agent.happiness for agent in agents) / len(agents)
        avg_health = sum(agent.health for agent in agents) / len(agents)
        avg_energy = sum(agent.energy for agent in agents) / len(agents)
        
        print(f"\n🤝 SOCIAL ANALYSIS:")
        print(f"  Total Messages: {total_messages}")
        print(f"  Messages per Agent: {total_messages/len(agents):.1f}")
        print(f"  Total Social Connections: {total_connections}")
        print(f"  Connections per Agent: {total_connections/len(agents):.1f}")
        
        print(f"\n❤️  FINAL WELLBEING:")
        print(f"  Average Health: {avg_health:.1f}%")
        print(f"  Average Happiness: {avg_happiness:.1f}%")
        print(f"  Average Energy: {avg_energy:.1f}%")
        
        # Show some interesting agent stories
        print(f"\n📖 AGENT STORIES:")
        
        # Most successful agent (by wealth)
        richest = max(agents, key=lambda a: a.wealth)
        print(f"  💰 Richest: {richest.agent_id}")
        print(f"     Wealth: ${richest.wealth:.2f}, Happiness: {richest.happiness:.1f}%")
        print(f"     Actions: {richest.actions_taken}, Messages: {richest.messages_sent}")
        print(f"     Personality: Social={richest.personality.get('social', 0):.2f}, "
              f"Ambitious={richest.personality.get('ambitious', 0):.2f}")
        
        # Happiest agent
        happiest = max(agents, key=lambda a: a.happiness)
        print(f"  😊 Happiest: {happiest.agent_id}")
        print(f"     Happiness: {happiest.happiness:.1f}%, Wealth: ${happiest.wealth:.2f}")
        print(f"     Social Connections: {happiest.social_connections}")
        print(f"     Personality: Social={happiest.personality.get('social', 0):.2f}, "
              f"Helpful={happiest.personality.get('helpful', 0):.2f}")
        
        # Most social agent
        most_social = max(agents, key=lambda a: a.social_connections)
        print(f"  🤝 Most Social: {most_social.agent_id}")
        print(f"     Connections: {most_social.social_connections}, Messages: {most_social.messages_sent}")
        print(f"     Happiness: {most_social.happiness:.1f}%, Wealth: ${most_social.wealth:.2f}")
        
        # Show final report metrics if available
        if final_report:
            print(f"\n📊 SIMULATION METRICS:")
            for key, value in final_report.items():
                if isinstance(value, (int, float)) and key != 'agents':
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        
    def export_results(self, final_report: Dict[str, Any]):
        """Export simulation results"""
        agents = list(self.simulator.agents.values())
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'num_agents': self.num_agents,
            'final_report': final_report,
            'agents': [
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
                    'memory_count': len(agent.memory)
                }
                for agent in agents
            ]
        }
        
        filename = f"society_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
            
        print(f"\n💾 RESULTS EXPORTED: {filename}")
        print(f"   Agents: {len(agents)}")
        print(f"   File size: {len(json.dumps(export_data, default=str))} characters")
        
    async def run_interactive_demo(self):
        """Run an interactive version of the demo"""
        print("🎮 INTERACTIVE SOCIETY DEMO")
        print("Commands: 'step [n]', 'status', 'agents', 'richest', 'happiest', 'export', 'quit'")
        print()
        
        self.simulator = EnhancedSocietySimulator(num_agents=20)  # Smaller for interactive
        
        print("Simulation initialized. Ready for commands!")
        
        while True:
            try:
                command = input("society> ").strip().lower()
                
                if command.startswith('step'):
                    # Parse number of steps
                    parts = command.split()
                    steps = int(parts[1]) if len(parts) > 1 else 1
                    
                    print(f"Running {steps} simulation step(s)...")
                    await self.simulator.run_simulation(steps=steps)
                    print(f"Completed {steps} step(s)")
                          
                elif command == 'status':
                    agents = list(self.simulator.agents.values())
                    active_agents = sum(1 for agent in agents if agent.health > 10)
                    total_wealth = sum(agent.wealth for agent in agents)
                    avg_happiness = sum(agent.happiness for agent in agents) / len(agents) if agents else 0
                    total_messages = sum(agent.messages_sent for agent in agents)
                    total_actions = sum(agent.actions_taken for agent in agents)
                    
                    print(f"📊 SIMULATION STATUS:")
                    print(f"  Active Agents: {active_agents}/{len(agents)}")
                    print(f"  Total Wealth: ${total_wealth:.2f}")
                    print(f"  Average Happiness: {avg_happiness:.1f}%")
                    print(f"  Total Messages: {total_messages}")
                    print(f"  Total Actions: {total_actions}")
                    
                elif command == 'agents':
                    agents = list(self.simulator.agents.values())[:5]  # Show first 5
                    print("👥 SAMPLE AGENTS:")
                    for agent in agents:
                        print(f"  {agent.agent_id}: "
                              f"Wealth=${agent.wealth:.1f}, "
                              f"Happiness={agent.happiness:.1f}%, "
                              f"Actions={agent.actions_taken}")
                        
                elif command == 'richest':
                    agents = list(self.simulator.agents.values())
                    if not agents:
                        print("No agents in simulation.")
                        continue
                    richest = max(agents, key=lambda a: a.wealth)
                    print(f"💰 RICHEST AGENT: {richest.agent_id}")
                    print(f"   Wealth: ${richest.wealth:.2f}")
                    print(f"   Happiness: {richest.happiness:.1f}%")
                    print(f"   Actions: {richest.actions_taken}")
                    print(f"   Social: {richest.personality.get('social', 0):.2f}")
                    
                elif command == 'happiest':
                    agents = list(self.simulator.agents.values())
                    happiest = max(agents, key=lambda a: a.happiness)
                    print(f"😊 HAPPIEST AGENT: {happiest.agent_id}")
                    print(f"   Happiness: {happiest.happiness:.1f}%")
                    print(f"   Wealth: ${happiest.wealth:.2f}")
                    print(f"   Connections: {happiest.social_connections}")
                    print(f"   Helpful: {happiest.personality.get('helpful', 0):.2f}")
                        
                elif command == 'export':
                    final_report = self.simulator._generate_final_report()
                    self.export_results(final_report)
                    
                elif command == 'quit':
                    print("Exiting interactive demo.")
                    break
                    
                else:
                    print("Available commands: step [n], status, agents, richest, happiest, export, quit")
                    
            except KeyboardInterrupt:
                print("\nInteractive demo terminated by user.")
                break
            except Exception as e:
                print(f"Error: {e}")

async def main():
    """Main demo function"""
    import sys
    
    demo = None # Initialize demo to None
    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
            demo = SimpleSocietyDemo(num_agents=20)
            await demo.run_interactive_demo()
        else:
            demo = SimpleSocietyDemo(num_agents=50)
            await demo.run_demo()
    except KeyboardInterrupt:
        print("\nSimulation terminated by user.")
    finally:
        if demo and demo.simulator: # Ensure simulator exists
             logger.info("Simulation ended. Final state might not be fully consistent if interrupted.")

if __name__ == "__main__":
    asyncio.run(main())