#!/usr/bin/env python3
"""
STEP 2: Systematic Scale Testing
===============================

Tests the enhanced agent system at different scales:
- 100 agents (baseline)
- 500 agents (medium scale)  
- 1000 agents (large scale)
- 2500 agents (maximum scale)

Measures:
- Decision quality and variety
- Performance metrics (time, memory)
- Emergent behaviors
- System stability
"""

import asyncio
import time
import json
import sqlite3
import psutil
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from dataclasses import asdict

# Import our enhanced intelligence
from step1_enhanced_intelligence import EnhancedIntelligence, PersonalityProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScaleTestAgent:
    """Simplified agent for scale testing"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.happiness = 0.5 + (hash(agent_id) % 100) / 200  # Deterministic but varied
        self.wealth = 1000 + (hash(agent_id) % 1000)
        self.energy = 0.3 + (hash(agent_id) % 70) / 100
        self.cooperation = 0.2 + (hash(agent_id) % 80) / 100
        self.innovation = 0.3 + (hash(agent_id) % 70) / 100
        self.reputation = 0.4 + (hash(agent_id) % 60) / 100
        
        # Track decisions
        self.decision_history = []
        self.learned_patterns = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for intelligence system"""
        return {
            'agent_id': self.agent_id,
            'happiness': self.happiness,
            'wealth': self.wealth,
            'energy': self.energy,
            'cooperation': self.cooperation,
            'innovation': self.innovation,
            'reputation': self.reputation,
            'decision_history': self.decision_history,
            'learned_patterns': self.learned_patterns
        }
    
    def update_from_decision(self, decision: Dict, outcome: Dict):
        """Update agent state from decision outcome"""
        self.decision_history.append(decision)
        
        # Apply outcome changes
        self.happiness += outcome.get('happiness_change', 0)
        self.wealth += outcome.get('wealth_change', 0)
        self.energy += outcome.get('energy_change', 0)
        self.cooperation += outcome.get('cooperation_change', 0)
        
        # Clamp values
        self.happiness = max(0, min(1, self.happiness))
        self.energy = max(0, min(1, self.energy))
        self.cooperation = max(0, min(1, self.cooperation))
        self.wealth = max(0, self.wealth)

class PerformanceMonitor:
    """Monitor system performance during scale tests"""
    
    def __init__(self):
        self.start_time = None
        self.memory_samples = []
        self.cpu_samples = []
        self.decision_times = []
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.memory_samples = []
        self.cpu_samples = []
        self.decision_times = []
    
    def sample_performance(self):
        """Take a performance sample"""
        process = psutil.Process(os.getpid())
        
        self.memory_samples.append({
            'timestamp': time.time() - self.start_time,
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent()
        })
        
        self.cpu_samples.append({
            'timestamp': time.time() - self.start_time,
            'cpu_percent': process.cpu_percent()
        })
    
    def record_decision_time(self, duration: float):
        """Record time taken for a decision"""
        self.decision_times.append(duration)
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        avg_memory = sum(s['memory_mb'] for s in self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
        max_memory = max(s['memory_mb'] for s in self.memory_samples) if self.memory_samples else 0
        
        avg_cpu = sum(s['cpu_percent'] for s in self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        
        avg_decision_time = sum(self.decision_times) / len(self.decision_times) if self.decision_times else 0
        
        return {
            'total_runtime_seconds': total_time,
            'avg_memory_mb': avg_memory,
            'max_memory_mb': max_memory,
            'avg_cpu_percent': avg_cpu,
            'avg_decision_time_ms': avg_decision_time * 1000,
            'total_decisions': len(self.decision_times),
            'decisions_per_second': len(self.decision_times) / total_time if total_time > 0 else 0
        }

class ScaleTestRunner:
    """Run systematic scale tests"""
    
    def __init__(self):
        self.intelligence = EnhancedIntelligence()
        self.test_results = {}
        
    async def run_scale_test(self, num_agents: int, num_steps: int = 5, 
                           test_name: str = None) -> Dict:
        """Run a scale test with specified parameters"""
        
        if not test_name:
            test_name = f"scale_test_{num_agents}_agents"
        
        print(f"\n🧪 Starting {test_name}")
        print(f"   Agents: {num_agents}, Steps: {num_steps}")
        
        # Initialize monitoring
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Create agents
        print("   📊 Creating agents...")
        agents = [ScaleTestAgent(f"agent_{i:04d}") for i in range(num_agents)]
        
        # Track simulation metrics
        simulation_data = {
            'decisions_by_action': {},
            'agent_states_over_time': [],
            'social_patterns': [],
            'emergent_behaviors': []
        }
        
        # Run simulation steps
        for step in range(num_steps):
            print(f"   ⚡ Step {step + 1}/{num_steps}")
            
            step_start = time.time()
            step_decisions = []
            
            # Process each agent
            for agent in agents:
                decision_start = time.time()
                
                # Get nearby agents (simple spatial model)
                nearby_agents = self._get_nearby_agents(agent, agents, radius=5)
                
                context = {
                    'nearby_agents': [a.to_dict() for a in nearby_agents],
                    'step': step,
                    'total_agents': num_agents
                }
                
                # Make decision using enhanced intelligence
                decision = self.intelligence.make_enhanced_decision(
                    agent.to_dict(), context
                )
                
                # Simulate outcome
                outcome = self._simulate_outcome(decision, agent, nearby_agents)
                
                # Update agent
                agent.update_from_decision(decision, outcome)
                
                # Update intelligence learning
                self.intelligence.update_from_outcome(agent.agent_id, decision, outcome)
                
                # Record metrics
                decision_time = time.time() - decision_start
                monitor.record_decision_time(decision_time)
                
                step_decisions.append({
                    'agent_id': agent.agent_id,
                    'action': decision['action'],
                    'confidence': decision['confidence'],
                    'reasoning': decision['reasoning']
                })
                
                # Track action frequency
                action = decision['action']
                if action not in simulation_data['decisions_by_action']:
                    simulation_data['decisions_by_action'][action] = 0
                simulation_data['decisions_by_action'][action] += 1
            
            # Sample performance
            monitor.sample_performance()
            
            # Analyze step results
            step_analysis = self._analyze_step(step_decisions, agents)
            simulation_data['agent_states_over_time'].append(step_analysis)
            
            step_time = time.time() - step_start
            print(f"     ⏱️  Step completed in {step_time:.2f}s")
        
        # Final analysis
        performance_summary = monitor.get_summary()
        behavioral_analysis = self._analyze_behaviors(simulation_data, agents)
        
        test_result = {
            'test_name': test_name,
            'parameters': {
                'num_agents': num_agents,
                'num_steps': num_steps,
                'timestamp': datetime.now().isoformat()
            },
            'performance': performance_summary,
            'behavioral_analysis': behavioral_analysis,
            'simulation_data': simulation_data
        }
        
        self.test_results[test_name] = test_result
        
        print(f"   ✅ {test_name} completed!")
        print(f"      Runtime: {performance_summary['total_runtime_seconds']:.1f}s")
        print(f"      Decisions/sec: {performance_summary['decisions_per_second']:.1f}")
        print(f"      Memory: {performance_summary['avg_memory_mb']:.1f}MB")
        
        return test_result
    
    def _get_nearby_agents(self, agent: ScaleTestAgent, all_agents: List[ScaleTestAgent], 
                          radius: int = 5) -> List[ScaleTestAgent]:
        """Get nearby agents (simple linear proximity)"""
        agent_index = int(agent.agent_id.split('_')[1])
        nearby = []
        
        for i in range(max(0, agent_index - radius), 
                      min(len(all_agents), agent_index + radius + 1)):
            if i != agent_index:
                nearby.append(all_agents[i])
        
        return nearby
    
    def _simulate_outcome(self, decision: Dict, agent: ScaleTestAgent, 
                         nearby_agents: List[ScaleTestAgent]) -> Dict:
        """Simulate realistic outcome from decision"""
        
        action = decision['action']
        confidence = decision['confidence']
        
        # Base outcome probabilities
        outcomes = {
            'cooperate': {
                'happiness_change': 0.05 * confidence,
                'wealth_change': 20 * confidence,
                'energy_change': -0.02,
                'cooperation_change': 0.01,
                'social_impact': 0.1
            },
            'compete': {
                'happiness_change': 0.02 * confidence - 0.03,
                'wealth_change': 50 * confidence - 20,
                'energy_change': -0.05,
                'cooperation_change': -0.01,
                'social_impact': -0.05
            },
            'innovate': {
                'happiness_change': 0.03 * confidence,
                'wealth_change': 80 * confidence - 30,
                'energy_change': -0.04,
                'cooperation_change': 0.0,
                'social_impact': 0.05
            },
            'socialize': {
                'happiness_change': 0.04 * confidence,
                'wealth_change': 0,
                'energy_change': -0.01,
                'cooperation_change': 0.02,
                'social_impact': 0.15
            },
            'rest': {
                'happiness_change': 0.02,
                'wealth_change': 0,
                'energy_change': 0.1,
                'cooperation_change': 0.0,
                'social_impact': 0.0
            },
            'trade': {
                'happiness_change': 0.01,
                'wealth_change': 30 * confidence,
                'energy_change': -0.02,
                'cooperation_change': 0.01,
                'social_impact': 0.05
            }
        }
        
        base_outcome = outcomes.get(action, outcomes['rest'])
        
        # Add social influence
        if nearby_agents:
            avg_cooperation = sum(a.cooperation for a in nearby_agents) / len(nearby_agents)
            social_bonus = (avg_cooperation - 0.5) * 0.1
            
            for key in base_outcome:
                if 'change' in key:
                    base_outcome[key] += social_bonus
        
        # Add some randomness
        import random
        for key in base_outcome:
            if 'change' in key:
                base_outcome[key] += random.uniform(-0.01, 0.01)
        
        return base_outcome
    
    def _analyze_step(self, decisions: List[Dict], agents: List[ScaleTestAgent]) -> Dict:
        """Analyze results from a simulation step"""
        
        # Decision distribution
        action_counts = {}
        confidence_by_action = {}
        
        for decision in decisions:
            action = decision['action']
            confidence = decision['confidence']
            
            if action not in action_counts:
                action_counts[action] = 0
                confidence_by_action[action] = []
            
            action_counts[action] += 1
            confidence_by_action[action].append(confidence)
        
        # Agent state statistics
        happiness_values = [a.happiness for a in agents]
        wealth_values = [a.wealth for a in agents]
        cooperation_values = [a.cooperation for a in agents]
        energy_values = [a.energy for a in agents]
        
        return {
            'action_distribution': action_counts,
            'avg_confidence_by_action': {
                action: sum(confidences) / len(confidences) 
                for action, confidences in confidence_by_action.items()
            },
            'agent_statistics': {
                'avg_happiness': sum(happiness_values) / len(happiness_values),
                'avg_wealth': sum(wealth_values) / len(wealth_values),
                'avg_cooperation': sum(cooperation_values) / len(cooperation_values),
                'avg_energy': sum(energy_values) / len(energy_values),
                'happiness_std': self._std_dev(happiness_values),
                'wealth_std': self._std_dev(wealth_values)
            }
        }
    
    def _analyze_behaviors(self, simulation_data: Dict, agents: List[ScaleTestAgent]) -> Dict:
        """Analyze emergent behaviors and patterns"""
        
        # Decision diversity
        total_decisions = sum(simulation_data['decisions_by_action'].values())
        action_diversity = len(simulation_data['decisions_by_action'])
        
        # Most common actions
        sorted_actions = sorted(
            simulation_data['decisions_by_action'].items(),
            key=lambda x: x[1], reverse=True
        )
        
        # Cooperation trends
        cooperation_over_time = []
        happiness_over_time = []
        
        for step_data in simulation_data['agent_states_over_time']:
            cooperation_over_time.append(step_data['agent_statistics']['avg_cooperation'])
            happiness_over_time.append(step_data['agent_statistics']['avg_happiness'])
        
        # Detect trends
        cooperation_trend = self._calculate_trend(cooperation_over_time)
        happiness_trend = self._calculate_trend(happiness_over_time)
        
        return {
            'decision_diversity': action_diversity,
            'total_decisions': total_decisions,
            'most_common_actions': sorted_actions[:3],
            'cooperation_trend': cooperation_trend,
            'happiness_trend': happiness_trend,
            'final_avg_cooperation': cooperation_over_time[-1] if cooperation_over_time else 0,
            'final_avg_happiness': happiness_over_time[-1] if happiness_over_time else 0,
            'behavioral_summary': self._generate_behavioral_summary(sorted_actions, cooperation_trend, happiness_trend)
        }
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
        
        start_avg = sum(values[:len(values)//3]) / (len(values)//3) if len(values) >= 3 else values[0]
        end_avg = sum(values[-len(values)//3:]) / (len(values)//3) if len(values) >= 3 else values[-1]
        
        change = end_avg - start_avg
        
        if change > 0.02:
            return "increasing"
        elif change < -0.02:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_behavioral_summary(self, sorted_actions: List, cooperation_trend: str, 
                                   happiness_trend: str) -> str:
        """Generate human-readable behavioral summary"""
        
        most_common = sorted_actions[0][0] if sorted_actions else "unknown"
        
        summary = f"Agents primarily chose '{most_common}' actions. "
        summary += f"Cooperation levels are {cooperation_trend} "
        summary += f"and happiness levels are {happiness_trend}."
        
        return summary
    
    async def run_full_scale_suite(self) -> Dict:
        """Run the complete scale testing suite"""
        
        print("🚀 Starting Complete Scale Testing Suite")
        print("=" * 50)
        
        test_scales = [
            (100, 5, "baseline_100_agents"),
            (500, 5, "medium_500_agents"),
            (1000, 3, "large_1000_agents"),
            (2500, 2, "maximum_2500_agents")
        ]
        
        suite_results = {}
        
        for num_agents, num_steps, test_name in test_scales:
            try:
                result = await self.run_scale_test(num_agents, num_steps, test_name)
                suite_results[test_name] = result
                
                # Brief cooldown between tests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}")
                suite_results[test_name] = {"error": str(e)}
        
        # Generate comparative analysis
        comparative_analysis = self._compare_scale_results(suite_results)
        
        final_results = {
            'suite_timestamp': datetime.now().isoformat(),
            'individual_tests': suite_results,
            'comparative_analysis': comparative_analysis
        }
        
        # Save results
        with open(f'scale_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print("\n🎯 Scale Testing Suite Complete!")
        print("=" * 50)
        self._print_summary(comparative_analysis)
        
        return final_results
    
    def _compare_scale_results(self, results: Dict) -> Dict:
        """Compare results across different scales"""
        
        comparison = {
            'performance_scaling': {},
            'behavioral_changes': {},
            'efficiency_metrics': {}
        }
        
        for test_name, result in results.items():
            if 'error' in result:
                continue
                
            num_agents = result['parameters']['num_agents']
            perf = result['performance']
            behavior = result['behavioral_analysis']
            
            comparison['performance_scaling'][num_agents] = {
                'decisions_per_second': perf['decisions_per_second'],
                'memory_mb': perf['avg_memory_mb'],
                'avg_decision_time_ms': perf['avg_decision_time_ms']
            }
            
            comparison['behavioral_changes'][num_agents] = {
                'cooperation_level': behavior['final_avg_cooperation'],
                'happiness_level': behavior['final_avg_happiness'],
                'decision_diversity': behavior['decision_diversity'],
                'most_common_action': behavior['most_common_actions'][0][0] if behavior['most_common_actions'] else 'none'
            }
            
            comparison['efficiency_metrics'][num_agents] = {
                'decisions_per_mb': perf['decisions_per_second'] / perf['avg_memory_mb'] if perf['avg_memory_mb'] > 0 else 0,
                'total_decisions': perf['total_decisions']
            }
        
        return comparison
    
    def _print_summary(self, analysis: Dict):
        """Print human-readable summary"""
        
        print("\n📊 SCALE TESTING SUMMARY")
        print("-" * 30)
        
        # Performance scaling
        print("\n⚡ Performance Scaling:")
        for agents, metrics in analysis['performance_scaling'].items():
            print(f"  {agents:4d} agents: {metrics['decisions_per_second']:6.1f} dec/sec, "
                  f"{metrics['memory_mb']:6.1f}MB, {metrics['avg_decision_time_ms']:5.1f}ms/dec")
        
        # Behavioral changes
        print("\n🧠 Behavioral Patterns:")
        for agents, behavior in analysis['behavioral_changes'].items():
            print(f"  {agents:4d} agents: cooperation={behavior['cooperation_level']:.2f}, "
                  f"happiness={behavior['happiness_level']:.2f}, "
                  f"favors '{behavior['most_common_action']}'")
        
        # Efficiency
        print("\n⚙️  Efficiency Metrics:")
        for agents, efficiency in analysis['efficiency_metrics'].items():
            print(f"  {agents:4d} agents: {efficiency['decisions_per_mb']:.1f} decisions/MB")

# Test with smaller scale first
async def main():
    """Run a quick test"""
    runner = ScaleTestRunner()
    result = await runner.run_scale_test(50, 3, "quick_test")
    print(f"\nTest completed: {result['test_name']}")
    return result

if __name__ == "__main__":
    asyncio.run(main()) 