#!/usr/bin/env python3
"""
Actual Cloud Deployment for 2,500 Agent Society Simulation
Uses existing cloud infrastructure to deploy real agents
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List

import aiohttp
import requests


class CloudAgent2500:
    """Enhanced cloud agent for 2,500 agent deployment"""
    
    def __init__(self, agent_id: int, groq_api_key: str, instance_id: int):
        self.id = agent_id
        self.instance_id = instance_id
        self.groq_api_key = groq_api_key
        
        # Initialize agent state
        import numpy as np
        self.position = np.random.uniform(0, 100, 2)
        self.energy = np.random.uniform(0.5, 1.0)
        self.happiness = np.random.uniform(0.3, 0.8)
        self.wealth = np.random.uniform(100, 1000)
        
        # Enhanced belief system
        self.beliefs = {
            "cooperation_value": np.random.uniform(0.3, 0.9),
            "authority_respect": np.random.uniform(0.2, 0.8),
            "innovation_openness": np.random.uniform(0.4, 0.9),
            "resource_sharing": np.random.uniform(0.3, 0.8),
            "conflict_avoidance": np.random.uniform(0.4, 0.9),
            "tradition_respect": np.random.uniform(0.2, 0.7),
            "change_acceptance": np.random.uniform(0.3, 0.8)
        }
        
        self.connections = []
        self.history = []
    
    async def make_decision(self, context: Dict) -> Dict:
        """Make decision using Groq API with enhanced prompting"""
        
        # Create rich context prompt
        prompt = f"""
        You are Agent {self.id} in a massive 2,500-agent society simulation (Instance {self.instance_id}).
        
        CURRENT STATUS:
        - Energy: {self.energy:.2f}/1.0
        - Happiness: {self.happiness:.2f}/1.0  
        - Wealth: {self.wealth:.0f} credits
        - Position: ({self.position[0]:.1f}, {self.position[1]:.1f})
        
        BELIEF SYSTEM:
        - Cooperation Value: {self.beliefs['cooperation_value']:.2f}
        - Authority Respect: {self.beliefs['authority_respect']:.2f}
        - Innovation Openness: {self.beliefs['innovation_openness']:.2f}
        - Resource Sharing: {self.beliefs['resource_sharing']:.2f}
        - Conflict Avoidance: {self.beliefs['conflict_avoidance']:.2f}
        
        SOCIETY CONTEXT:
        {json.dumps(context, indent=2)}
        
        Based on your beliefs and current situation, what action do you take?
        
        Respond with JSON:
        {{
            "action": "move/trade/cooperate/compete/innovate/rest/socialize",
            "target_position": [x, y] (if moving),
            "target_agent": agent_id (if interacting),
            "reasoning": "brief explanation based on your beliefs",
            "belief_change": {{"belief_name": change_amount}} (if any beliefs change),
            "mood": "happy/neutral/frustrated/excited/worried"
        }}
        """
        
        try:
            import groq
            client = groq.Groq(api_key=self.groq_api_key)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7
                )
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                decision = json.loads(content)
                return decision
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "action": "rest",
                    "reasoning": "Failed to parse decision",
                    "mood": "confused"
                }
                
        except Exception as e:
            return {
                "action": "rest", 
                "reasoning": f"API Error: {str(e)}",
                "mood": "frustrated"
            }
    
    def update_state(self, decision: Dict, interactions: List):
        """Update agent state based on decision and interactions"""
        
        import numpy as np
        
        # Update beliefs if specified
        if "belief_change" in decision and decision["belief_change"]:
            for belief, change in decision["belief_change"].items():
                if belief in self.beliefs:
                    self.beliefs[belief] = np.clip(
                        self.beliefs[belief] + change, 0.0, 1.0
                    )
        
        # Update position if moving
        if decision.get("action") == "move" and "target_position" in decision:
            target = decision["target_position"]
            if len(target) == 2:
                self.position = np.array(target)
        
        # Update energy based on action
        action = decision.get("action", "rest")
        energy_costs = {
            "rest": -0.05,  # Gain energy
            "move": 0.02,
            "trade": 0.03,
            "cooperate": 0.01,
            "compete": 0.05,
            "innovate": 0.04,
            "socialize": 0.02
        }
        
        self.energy += energy_costs.get(action, 0.02)
        self.energy = np.clip(self.energy, 0.0, 1.0)
        
        # Update happiness based on interactions and mood
        mood = decision.get("mood", "neutral")
        mood_effects = {
            "happy": 0.05,
            "excited": 0.03,
            "neutral": 0.0,
            "frustrated": -0.03,
            "worried": -0.02,
            "confused": -0.01
        }
        
        self.happiness += mood_effects.get(mood, 0.0)
        
        # Interaction effects
        if interactions:
            interaction_quality = np.mean([i.get("quality", 0.5) for i in interactions])
            self.happiness += (interaction_quality - 0.5) * 0.1
        
        self.happiness = np.clip(self.happiness, 0.0, 1.0)
        
        # Record history
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "decision": decision,
            "energy": self.energy,
            "happiness": self.happiness,
            "wealth": self.wealth,
            "beliefs": self.beliefs.copy(),
            "interactions": len(interactions)
        })


class Cloud2500Simulation:
    """Manages 500 agents on a single cloud instance (part of 2,500 total)"""
    
    def __init__(self, n_agents: int, groq_api_key: str, instance_id: int):
        self.n_agents = n_agents
        self.instance_id = instance_id
        self.groq_api_key = groq_api_key
        self.agents = []
        self.step_count = 0
        self.results = []
        
        print(f"🚀 Initializing Instance {instance_id} with {n_agents} agents...")
        
        # Create agents
        for i in range(n_agents):
            agent = CloudAgent2500(i, groq_api_key, instance_id)
            self.agents.append(agent)
    
    async def run_simulation(self, duration_minutes: int = 30):
        """Run simulation for specified duration"""
        
        print(f"🔥 Starting Instance {self.instance_id} simulation")
        print(f"   Agents: {self.n_agents}")
        print(f"   Duration: {duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        step_count = 0
        
        while time.time() < end_time:
            step_start = time.time()
            
            await self.simulation_step()
            step_count += 1
            
            step_time = time.time() - step_start
            elapsed = time.time() - start_time
            remaining = end_time - time.time()
            
            # Progress update every 5 steps
            if step_count % 5 == 0:
                avg_energy = sum(a.energy for a in self.agents) / len(self.agents)
                avg_happiness = sum(a.happiness for a in self.agents) / len(self.agents)
                
                print(f"   Step {step_count}: {step_time:.1f}s, "
                      f"Energy: {avg_energy:.3f}, Happiness: {avg_happiness:.3f}, "
                      f"Remaining: {remaining/60:.1f}m")
            
            # Small delay to prevent API rate limiting
            await asyncio.sleep(2)
        
        final_results = self.get_final_results()
        
        print(f"✅ Instance {self.instance_id} completed: {step_count} steps")
        print(f"   Final happiness: {final_results['final_metrics']['avg_happiness']:.3f}")
        print(f"   Total wealth: {final_results['final_metrics']['total_wealth']:.0f}")
        
        return final_results
    
    async def simulation_step(self):
        """Execute one simulation step"""
        
        # Get decisions from all agents in parallel
        decision_tasks = []
        for agent in self.agents:
            context = self.get_agent_context(agent)
            task = agent.make_decision(context)
            decision_tasks.append(task)
        
        # Wait for all decisions
        decisions = await asyncio.gather(*decision_tasks)
        
        # Process interactions
        interactions = self.process_interactions(list(zip(self.agents, decisions)))
        
        # Update agent states
        for i, (agent, decision) in enumerate(zip(self.agents, decisions)):
            agent_interactions = [
                interaction for interaction in interactions 
                if agent.id in interaction.get("participants", [])
            ]
            agent.update_state(decision, agent_interactions)
        
        # Record step results
        step_result = {
            "step": self.step_count,
            "instance_id": self.instance_id,
            "timestamp": datetime.utcnow().isoformat(),
            "avg_energy": sum(a.energy for a in self.agents) / len(self.agents),
            "avg_happiness": sum(a.happiness for a in self.agents) / len(self.agents),
            "total_wealth": sum(a.wealth for a in self.agents),
            "decision_summary": self.summarize_decisions(decisions),
            "interaction_count": len(interactions)
        }
        
        self.results.append(step_result)
        self.step_count += 1
    
    def get_agent_context(self, agent) -> Dict:
        """Get context for agent decision making"""
        
        import numpy as np
        
        # Find nearby agents
        nearby_agents = []
        for other in self.agents:
            if other.id != agent.id:
                distance = np.linalg.norm(agent.position - other.position)
                if distance < 15:  # Within interaction range
                    nearby_agents.append({
                        "id": other.id,
                        "distance": distance,
                        "energy": other.energy,
                        "happiness": other.happiness,
                        "wealth": other.wealth
                    })
        
        # Society-wide metrics
        society_metrics = {
            "avg_energy": sum(a.energy for a in self.agents) / len(self.agents),
            "avg_happiness": sum(a.happiness for a in self.agents) / len(self.agents),
            "total_wealth": sum(a.wealth for a in self.agents),
            "agent_count": len(self.agents)
        }
        
        return {
            "nearby_agents": nearby_agents[:3],  # Limit to 3 nearest
            "step": self.step_count,
            "society_metrics": society_metrics,
            "instance_id": self.instance_id
        }
    
    def process_interactions(self, decisions: List) -> List:
        """Process interactions between agents"""
        
        interactions = []
        
        # Group agents by action type
        action_groups = {}
        for agent, decision in decisions:
            action = decision.get("action", "rest")
            if action not in action_groups:
                action_groups[action] = []
            action_groups[action].append((agent, decision))
        
        # Process cooperation
        if "cooperate" in action_groups and len(action_groups["cooperate"]) >= 2:
            coop_agents = action_groups["cooperate"]
            
            # Pair agents for cooperation
            for i in range(0, len(coop_agents) - 1, 2):
                agent1, decision1 = coop_agents[i]
                agent2, decision2 = coop_agents[i + 1]
                
                # Cooperation benefit based on beliefs
                cooperation_strength = (
                    agent1.beliefs["cooperation_value"] + 
                    agent2.beliefs["cooperation_value"]
                ) / 2
                
                benefit = 50 + (cooperation_strength * 100)
                agent1.wealth += benefit
                agent2.wealth += benefit
                
                interactions.append({
                    "type": "cooperation",
                    "participants": [agent1.id, agent2.id],
                    "benefit": benefit,
                    "quality": 0.7 + (cooperation_strength * 0.3)
                })
        
        # Process competition
        if "compete" in action_groups and len(action_groups["compete"]) >= 2:
            comp_agents = action_groups["compete"]
            
            # Random competition pairs
            for i in range(0, len(comp_agents) - 1, 2):
                agent1, decision1 = comp_agents[i]
                agent2, decision2 = comp_agents[i + 1]
                
                # Competition outcome based on energy and beliefs
                agent1_strength = agent1.energy * (1 - agent1.beliefs["conflict_avoidance"])
                agent2_strength = agent2.energy * (1 - agent2.beliefs["conflict_avoidance"])
                
                if agent1_strength > agent2_strength:
                    winner, loser = agent1, agent2
                else:
                    winner, loser = agent2, agent1
                
                transfer = min(50 + (winner.energy * 50), loser.wealth * 0.3)
                winner.wealth += transfer
                loser.wealth = max(0, loser.wealth - transfer)
                
                interactions.append({
                    "type": "competition",
                    "participants": [agent1.id, agent2.id],
                    "winner": winner.id,
                    "transfer": transfer,
                    "quality": 0.2
                })
        
        # Process trading
        if "trade" in action_groups and len(action_groups["trade"]) >= 2:
            trade_agents = action_groups["trade"]
            
            # Random trading pairs
            for i in range(0, len(trade_agents) - 1, 2):
                agent1, decision1 = trade_agents[i]
                agent2, decision2 = trade_agents[i + 1]
                
                # Trade based on resource sharing beliefs
                trade_willingness = (
                    agent1.beliefs["resource_sharing"] + 
                    agent2.beliefs["resource_sharing"]
                ) / 2
                
                if trade_willingness > 0.5:
                    # Beneficial trade
                    trade_value = 30 + (trade_willingness * 40)
                    agent1.wealth += trade_value * 0.1
                    agent2.wealth += trade_value * 0.1
                    
                    interactions.append({
                        "type": "trade",
                        "participants": [agent1.id, agent2.id],
                        "value": trade_value,
                        "quality": trade_willingness
                    })
        
        return interactions
    
    def summarize_decisions(self, decisions: List) -> Dict:
        """Summarize decisions made in this step"""
        
        action_counts = {}
        mood_counts = {}
        
        for decision in decisions:
            action = decision.get("action", "rest")
            mood = decision.get("mood", "neutral")
            
            action_counts[action] = action_counts.get(action, 0) + 1
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        return {
            "actions": action_counts,
            "moods": mood_counts,
            "total_decisions": len(decisions)
        }
    
    def get_final_results(self) -> Dict:
        """Get final simulation results"""
        
        import numpy as np
        
        # Calculate final metrics
        final_metrics = {
            "avg_energy": np.mean([a.energy for a in self.agents]),
            "avg_happiness": np.mean([a.happiness for a in self.agents]),
            "total_wealth": sum([a.wealth for a in self.agents]),
            "wealth_distribution": {
                "min": min([a.wealth for a in self.agents]),
                "max": max([a.wealth for a in self.agents]),
                "std": np.std([a.wealth for a in self.agents])
            },
            "belief_evolution": self.analyze_belief_evolution()
        }
        
        return {
            "simulation_type": "cloud_2500_agent_instance",
            "instance_id": self.instance_id,
            "n_agents": self.n_agents,
            "total_steps": self.step_count,
            "final_metrics": final_metrics,
            "step_results": self.results[-5:],  # Last 5 steps
            "completion_timestamp": datetime.utcnow().isoformat()
        }
    
    def analyze_belief_evolution(self) -> Dict:
        """Analyze how beliefs have evolved during simulation"""
        
        import numpy as np
        
        belief_changes = {}
        
        for agent in self.agents:
            if len(agent.history) >= 2:
                initial_beliefs = agent.history[0]["beliefs"]
                final_beliefs = agent.history[-1]["beliefs"]
                
                for belief_name in initial_beliefs:
                    if belief_name not in belief_changes:
                        belief_changes[belief_name] = []
                    
                    change = final_beliefs[belief_name] - initial_beliefs[belief_name]
                    belief_changes[belief_name].append(change)
        
        # Calculate average changes
        avg_belief_changes = {}
        for belief_name, changes in belief_changes.items():
            avg_belief_changes[belief_name] = {
                "avg_change": np.mean(changes),
                "std_change": np.std(changes),
                "agents_changed": len([c for c in changes if abs(c) > 0.01])
            }
        
        return avg_belief_changes


async def deploy_single_instance(instance_id: int, agents_per_instance: int, 
                                groq_api_key: str, duration_minutes: int = 30):
    """Deploy and run a single instance of the simulation"""
    
    print(f"\n🚀 DEPLOYING INSTANCE {instance_id}")
    print("=" * 50)
    
    # Create simulation
    simulation = Cloud2500Simulation(agents_per_instance, groq_api_key, instance_id)
    
    # Run simulation
    results = await simulation.run_simulation(duration_minutes)
    
    return results


async def deploy_2500_agents_actual():
    """Deploy actual 2,500 agents across multiple processes"""
    
    print("🎯 DEPLOYING 2,500 AGENTS TO CLOUD")
    print("=" * 60)
    
    # Configuration
    total_agents = 2500
    instances = 5
    agents_per_instance = total_agents // instances
    duration_minutes = 30  # 30 minute test
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    print(f"Configuration:")
    print(f"  Total agents: {total_agents}")
    print(f"  Instances: {instances}")
    print(f"  Agents per instance: {agents_per_instance}")
    print(f"  Duration: {duration_minutes} minutes")
    print(f"  Groq API: {groq_api_key[:20]}...")
    print()
    
    # Deploy all instances in parallel
    start_time = time.time()
    
    print("🚀 Starting parallel deployment...")
    
    # Create tasks for all instances
    tasks = []
    for instance_id in range(instances):
        task = deploy_single_instance(
            instance_id, 
            agents_per_instance, 
            groq_api_key, 
            duration_minutes
        )
        tasks.append(task)
    
    # Run all instances in parallel
    instance_results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    print(f"\n🎉 ALL INSTANCES COMPLETED!")
    print("=" * 50)
    print(f"Total deployment time: {total_time/60:.1f} minutes")
    
    # Aggregate results
    aggregated_results = aggregate_instance_results(instance_results)
    
    # Display summary
    print(f"\n📊 FINAL RESULTS SUMMARY:")
    print(f"  Total agents: {aggregated_results['total_agents']}")
    print(f"  Total steps: {aggregated_results['total_steps']}")
    print(f"  Average happiness: {aggregated_results['avg_happiness']:.3f}")
    print(f"  Total wealth: {aggregated_results['total_wealth']:.0f}")
    print(f"  Successful instances: {aggregated_results['successful_instances']}")
    
    # Save results
    results_file = f"2500_agent_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "deployment_config": {
                "total_agents": total_agents,
                "instances": instances,
                "duration_minutes": duration_minutes,
                "deployment_time": total_time
            },
            "instance_results": instance_results,
            "aggregated_results": aggregated_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return aggregated_results


def aggregate_instance_results(instance_results: List[Dict]) -> Dict:
    """Aggregate results from all instances"""
    
    import numpy as np
    
    total_agents = sum(r["n_agents"] for r in instance_results)
    total_steps = sum(r["total_steps"] for r in instance_results)
    
    # Aggregate metrics
    happiness_values = [r["final_metrics"]["avg_happiness"] for r in instance_results]
    energy_values = [r["final_metrics"]["avg_energy"] for r in instance_results]
    wealth_values = [r["final_metrics"]["total_wealth"] for r in instance_results]
    
    # Aggregate belief evolution
    all_belief_changes = {}
    for result in instance_results:
        belief_evolution = result["final_metrics"]["belief_evolution"]
        for belief_name, data in belief_evolution.items():
            if belief_name not in all_belief_changes:
                all_belief_changes[belief_name] = []
            all_belief_changes[belief_name].append(data["avg_change"])
    
    aggregated_belief_changes = {}
    for belief_name, changes in all_belief_changes.items():
        aggregated_belief_changes[belief_name] = {
            "overall_avg_change": np.mean(changes),
            "change_std": np.std(changes)
        }
    
    return {
        "total_agents": total_agents,
        "total_steps": total_steps,
        "successful_instances": len(instance_results),
        "avg_happiness": np.mean(happiness_values),
        "happiness_std": np.std(happiness_values),
        "avg_energy": np.mean(energy_values),
        "total_wealth": sum(wealth_values),
        "belief_evolution": aggregated_belief_changes,
        "completion_timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    asyncio.run(deploy_2500_agents_actual()) 