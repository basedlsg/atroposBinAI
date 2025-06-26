#!/usr/bin/env python3
"""
Local LLM Fallback System
========================

Provides local LLM capabilities when API rate limits are hit,
allowing continued development and testing of the God Portal system.
"""

import json
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class LocalLLMFallback:
    """
    Fallback system that simulates LLM responses locally when APIs are unavailable.
    Uses sophisticated rule-based logic to maintain realistic agent behavior.
    """
    
    def __init__(self):
        self.decision_templates = self._load_decision_templates()
        self.personality_traits = self._generate_personality_traits()
        self.context_memory = {}
        
    def _load_decision_templates(self) -> Dict[str, List[Dict]]:
        """Load decision templates for different agent personalities"""
        return {
            "optimistic": [
                {"action": "WORK", "reasoning": "I feel energetic and ready to be productive today!", "happiness_mod": 0.02},
                {"action": "SOCIALIZE", "reasoning": "Meeting new people always brightens my day.", "happiness_mod": 0.05},
                {"action": "INNOVATE", "reasoning": "I have a great idea that could change everything!", "happiness_mod": 0.03},
                {"action": "REST", "reasoning": "Taking time to recharge will help me be more effective.", "happiness_mod": 0.04}
            ],
            
            "pragmatic": [
                {"action": "WORK", "reasoning": "Steady progress towards my goals is what matters most.", "happiness_mod": 0.01},
                {"action": "SOCIALIZE", "reasoning": "Building relationships is an investment in my future.", "happiness_mod": 0.02},
                {"action": "INNOVATE", "reasoning": "This calculated risk could pay off significantly.", "happiness_mod": 0.01},
                {"action": "REST", "reasoning": "I need to maintain my energy levels efficiently.", "happiness_mod": 0.02}
            ],
            
            "cautious": [
                {"action": "WORK", "reasoning": "Consistent work is the safest path to security.", "happiness_mod": 0.01},
                {"action": "SOCIALIZE", "reasoning": "I should maintain my social connections carefully.", "happiness_mod": 0.02},
                {"action": "INNOVATE", "reasoning": "Maybe a small, safe innovation could work.", "happiness_mod": -0.01},
                {"action": "REST", "reasoning": "I don't want to risk burning out from overwork.", "happiness_mod": 0.03}
            ],
            
            "ambitious": [
                {"action": "WORK", "reasoning": "Every hour of work brings me closer to my dreams!", "happiness_mod": 0.03},
                {"action": "SOCIALIZE", "reasoning": "Networking is key to unlocking new opportunities.", "happiness_mod": 0.02},
                {"action": "INNOVATE", "reasoning": "Bold moves are what separate leaders from followers!", "happiness_mod": 0.04},
                {"action": "REST", "reasoning": "Strategic rest will fuel my next big push.", "happiness_mod": 0.01}
            ]
        }
    
    def _generate_personality_traits(self) -> Dict[int, str]:
        """Generate personality types for agents"""
        personalities = ["optimistic", "pragmatic", "cautious", "ambitious"]
        return {i: random.choice(personalities) for i in range(3000)}  # Support up to 3000 agents
    
    def make_agent_decision(self, agent_id: int, current_state: Dict[str, float], 
                          recent_actions: List[str] = None) -> Dict[str, Any]:
        """
        Generate a contextually appropriate decision for an agent using local logic.
        This maintains the sophistication of LLM decisions without API calls.
        """
        
        # Get agent personality
        personality = self.personality_traits.get(agent_id, "pragmatic")
        templates = self.decision_templates[personality]
        
        # Context-aware decision making
        happiness = current_state.get('happiness', 0.5)
        wealth = current_state.get('wealth', 1000)
        cooperation = current_state.get('cooperation', 0.5)
        innovation = current_state.get('innovation', 0.5)
        
        # Decision logic based on current state
        if happiness < 0.3:
            # Low happiness - prioritize rest or socializing
            candidates = [t for t in templates if t['action'] in ['REST', 'SOCIALIZE']]
        elif wealth < 500:
            # Low wealth - prioritize work
            candidates = [t for t in templates if t['action'] == 'WORK']
        elif innovation < 0.4 and random.random() < 0.3:
            # Low innovation - occasionally try to innovate
            candidates = [t for t in templates if t['action'] == 'INNOVATE']
        else:
            # Normal state - all actions available
            candidates = templates
        
        # Avoid repetitive actions
        if recent_actions:
            last_action = recent_actions[-1] if recent_actions else None
            if last_action and len([a for a in recent_actions[-3:] if a == last_action]) >= 2:
                # Avoid doing the same thing 3 times in a row
                candidates = [t for t in candidates if t['action'] != last_action]
        
        # Select decision
        if not candidates:
            candidates = templates  # Fallback to all options
        
        base_decision = random.choice(candidates)
        
        # Add contextual reasoning
        reasoning = self._enhance_reasoning(base_decision['reasoning'], current_state, personality)
        
        return {
            "action": base_decision['action'],
            "reasoning": reasoning,
            "confidence": random.uniform(0.7, 0.95),
            "personality": personality,
            "local_llm": True  # Flag to indicate this was generated locally
        }
    
    def _enhance_reasoning(self, base_reasoning: str, state: Dict[str, float], personality: str) -> str:
        """Enhance reasoning with state-specific context"""
        
        enhancements = []
        
        happiness = state.get('happiness', 0.5)
        wealth = state.get('wealth', 1000)
        
        if happiness > 0.8:
            enhancements.append("I'm feeling particularly positive today.")
        elif happiness < 0.3:
            enhancements.append("I need to focus on improving my wellbeing.")
        
        if wealth > 1500:
            enhancements.append("My financial situation gives me flexibility.")
        elif wealth < 600:
            enhancements.append("I need to be mindful of my resources.")
        
        if personality == "optimistic":
            enhancements.append("I believe this will lead to great outcomes!")
        elif personality == "cautious":
            enhancements.append("I've thought this through carefully.")
        
        if enhancements:
            return f"{base_reasoning} {random.choice(enhancements)}"
        else:
            return base_reasoning

class LocalSimulationRunner:
    """Run simulations using local LLM fallback when APIs are unavailable"""
    
    def __init__(self):
        self.local_llm = LocalLLMFallback()
        self.simulation_start = datetime.now()
        
    async def run_local_simulation(self, num_agents: int = 100, steps: int = 10) -> Dict[str, Any]:
        """
        Run a smaller-scale simulation using local LLM fallback.
        This allows continued development and testing without API dependencies.
        """
        
        print(f"🏠 Starting LOCAL simulation: {num_agents} agents, {steps} steps")
        print("   (Using local LLM fallback due to API rate limits)")
        
        start_time = time.time()
        
        # Initialize agents with random starting states
        agents = []
        for i in range(num_agents):
            agent = {
                "id": i,
                "happiness": random.uniform(0.3, 0.7),
                "wealth": random.uniform(800, 1200),
                "cooperation": random.uniform(0.4, 0.8),
                "innovation": random.uniform(0.3, 0.7),
                "action_history": [],
                "stories": []
            }
            agents.append(agent)
        
        # Run simulation steps
        for step in range(steps):
            print(f"  📈 Step {step + 1}/{steps}")
            
            step_stories = []
            
            for agent in agents:
                # Get recent actions for context
                recent_actions = agent["action_history"][-3:] if agent["action_history"] else []
                
                # Make decision using local LLM
                decision = self.local_llm.make_agent_decision(
                    agent["id"],
                    {
                        "happiness": agent["happiness"],
                        "wealth": agent["wealth"],
                        "cooperation": agent["cooperation"],
                        "innovation": agent["innovation"]
                    },
                    recent_actions
                )
                
                # Apply decision effects
                self._apply_decision_effects(agent, decision)
                
                # Record action and story
                agent["action_history"].append(decision["action"])
                story = f"Agent {agent['id']} chose to {decision['action'].lower()}: {decision['reasoning']}"
                agent["stories"].append(story)
                step_stories.append(story)
            
            # Show some sample stories
            if step_stories:
                sample_stories = random.sample(step_stories, min(3, len(step_stories)))
                for story in sample_stories:
                    print(f"    💭 {story}")
        
        # Calculate final metrics
        runtime = time.time() - start_time
        results = self._calculate_local_results(agents, runtime)
        
        print(f"✅ Local simulation completed in {runtime:.1f} seconds")
        return results
    
    def _apply_decision_effects(self, agent: Dict, decision: Dict):
        """Apply the effects of an agent's decision to their state"""
        
        action = decision["action"]
        
        if action == "WORK":
            wealth_gain = random.uniform(40, 120)
            happiness_change = random.uniform(-0.03, 0.02)
            agent["wealth"] += wealth_gain
            agent["happiness"] = max(0, min(1, agent["happiness"] + happiness_change))
            
        elif action == "SOCIALIZE":
            happiness_gain = random.uniform(0.02, 0.06)
            cooperation_gain = random.uniform(0.01, 0.04)
            wealth_cost = random.uniform(10, 25)
            agent["happiness"] = min(1, agent["happiness"] + happiness_gain)
            agent["cooperation"] = min(1, agent["cooperation"] + cooperation_gain)
            agent["wealth"] = max(0, agent["wealth"] - wealth_cost)
            
        elif action == "INNOVATE":
            innovation_change = random.uniform(-0.02, 0.08)
            wealth_change = random.uniform(-40, 80)
            agent["innovation"] = max(0, min(1, agent["innovation"] + innovation_change))
            agent["wealth"] = max(0, agent["wealth"] + wealth_change)
            
        else:  # REST
            happiness_gain = random.uniform(0.02, 0.05)
            agent["happiness"] = min(1, agent["happiness"] + happiness_gain)
    
    def _calculate_local_results(self, agents: List[Dict], runtime: float) -> Dict[str, Any]:
        """Calculate results from local simulation"""
        
        total_agents = len(agents)
        avg_happiness = sum(a["happiness"] for a in agents) / total_agents
        total_wealth = sum(a["wealth"] for a in agents)
        avg_cooperation = sum(a["cooperation"] for a in agents) / total_agents
        avg_innovation = sum(a["innovation"] for a in agents) / total_agents
        
        # Count action types
        all_actions = []
        for agent in agents:
            all_actions.extend(agent["action_history"])
        
        action_counts = {}
        for action in all_actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "simulation_type": "LOCAL_LLM_FALLBACK",
            "total_agents": total_agents,
            "total_runtime_seconds": runtime,
            "avg_happiness": avg_happiness,
            "total_wealth": total_wealth,
            "avg_wealth": total_wealth / total_agents,
            "final_beliefs": {
                "avg_cooperation": avg_cooperation,
                "avg_innovation": avg_innovation
            },
            "action_distribution": action_counts,
            "success_rate": 1.0,  # Local simulation always succeeds
            "api_calls_made": 0,  # No API calls used
            "cost": 0.0,  # No cost for local simulation
            "agents_sample": agents[:5]  # Sample of agent final states
        }

def main():
    """Demonstrate local LLM fallback capabilities"""
    
    print("🏠 God Portal Local LLM Fallback System")
    print("=" * 50)
    print("This system allows continued development when API rate limits are hit.")
    print("Using sophisticated rule-based logic to maintain realistic agent behavior.\n")
    
    runner = LocalSimulationRunner()
    
    # Run a demonstration simulation
    import asyncio
    results = asyncio.run(runner.run_local_simulation(num_agents=50, steps=8))
    
    # Display results
    print("\n📊 LOCAL SIMULATION RESULTS:")
    print(f"  🤖 Agents: {results['total_agents']}")
    print(f"  ⏱️  Runtime: {results['total_runtime_seconds']:.1f} seconds")
    print(f"  😊 Avg Happiness: {results['avg_happiness']:.3f}/1.0")
    print(f"  💰 Total Wealth: {results['total_wealth']:,.0f} credits")
    print(f"  🤝 Cooperation: {results['final_beliefs']['avg_cooperation']:.3f}/1.0")
    print(f"  💡 Innovation: {results['final_beliefs']['avg_innovation']:.3f}/1.0")
    print(f"  💸 Cost: ${results['cost']:.2f} (FREE!)")
    
    print(f"\n📈 Action Distribution:")
    for action, count in results['action_distribution'].items():
        percentage = (count / sum(results['action_distribution'].values())) * 100
        print(f"  {action}: {count} ({percentage:.1f}%)")
    
    print(f"\n💡 Sample Agent Final States:")
    for i, agent in enumerate(results['agents_sample'][:3]):
        print(f"  Agent {agent['id']}: H={agent['happiness']:.2f}, W={agent['wealth']:.0f}, C={agent['cooperation']:.2f}, I={agent['innovation']:.2f}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"local_simulation_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    print("\n🚀 NEXT STEPS:")
    print("1. Use this local system for continued development")
    print("2. Implement multi-provider API support")
    print("3. Scale up once rate limits reset")
    print("4. Consider upgrading to paid API tiers for production")

if __name__ == "__main__":
    main() 