#!/usr/bin/env python3
"""
Enhanced Multi-Agent System with True AI Intelligence
====================================================

Phase 1-5 Implementation:
- Multi-provider API management
- Intelligent agent decision-making
- Agent-to-agent interactions
- Memory and learning
- Cloud-ready scalable architecture
"""

import asyncio
import json
import time
import random
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import aiohttp
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Enhanced agent state with memory and personality"""
    agent_id: str
    happiness: float
    wealth: float
    cooperation: float
    innovation: float
    energy: float
    reputation: float
    
    # Personality traits
    risk_tolerance: float
    social_preference: float
    ambition: float
    
    # Memory and learning
    decision_history: List[Dict] = None
    social_network: List[str] = None
    learned_patterns: Dict[str, float] = None
    last_interaction: Optional[datetime] = None
    
    def __post_init__(self):
        if self.decision_history is None:
            self.decision_history = []
        if self.social_network is None:
            self.social_network = []
        if self.learned_patterns is None:
            self.learned_patterns = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)

class MultiProviderAPIManager:
    """Manages multiple AI API providers with intelligent fallback"""
    
    def __init__(self):
        self.providers = {
            'groq': {
                'client': None,
                'api_key': os.getenv('GROQ_API_KEY'),
                'model': 'llama-3.1-8b-instant',
                'daily_limit': 500,
                'calls_today': 0,
                'cost_per_1k': 0.0,
                'active': True
            },
            'openai': {
                'client': None,
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': 'gpt-3.5-turbo',
                'daily_limit': 1000,
                'calls_today': 0,
                'cost_per_1k': 0.002,
                'active': bool(os.getenv('OPENAI_API_KEY'))
            },
            'anthropic': {
                'client': None,
                'api_key': os.getenv('ANTHROPIC_API_KEY'),
                'model': 'claude-3-haiku-20240307',
                'daily_limit': 2000,
                'calls_today': 0,
                'cost_per_1k': 0.001,
                'active': bool(os.getenv('ANTHROPIC_API_KEY'))
            }
        }
        
        self.setup_clients()
        self.request_queue = asyncio.Queue()
        self.rate_limiter = {}
    
    def setup_clients(self):
        """Initialize API clients"""
        try:
            if self.providers['groq']['active']:
                import groq
                self.providers['groq']['client'] = groq.Groq(
                    api_key=self.providers['groq']['api_key']
                )
        except ImportError:
            logger.warning("Groq not available")
            self.providers['groq']['active'] = False
        
        # Add other providers as needed
        logger.info(f"Active providers: {[k for k, v in self.providers.items() if v['active']]}")
    
    async def make_decision_request(self, agent: AgentState, context: Dict) -> Optional[Dict]:
        """Make AI decision request with intelligent provider selection"""
        
        # Select best available provider
        provider_name = self.select_optimal_provider()
        if not provider_name:
            return self.intelligent_fallback(agent, context)
        
        provider = self.providers[provider_name]
        
        # Rate limiting
        await self.apply_rate_limit(provider_name)
        
        try:
            prompt = self.create_decision_prompt(agent, context)
            
            if provider_name == 'groq':
                response = provider['client'].chat.completions.create(
                    model=provider['model'],
                    messages=[
                        {"role": "system", "content": self.get_system_prompt(agent)},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7 + (agent.risk_tolerance * 0.3)
                )
                
                content = response.choices[0].message.content.strip()
                decision = self.parse_ai_response(content, provider_name)
                
                provider['calls_today'] += 1
                return decision
                
        except Exception as e:
            logger.warning(f"API call failed for {provider_name}: {e}")
            return self.intelligent_fallback(agent, context)
        
        return None
    
    def select_optimal_provider(self) -> Optional[str]:
        """Select the best available provider based on limits and cost"""
        available = []
        
        for name, provider in self.providers.items():
            if (provider['active'] and 
                provider['calls_today'] < provider['daily_limit']):
                available.append((name, provider['cost_per_1k']))
        
        if not available:
            return None
        
        # Sort by cost (free first)
        available.sort(key=lambda x: x[1])
        return available[0][0]
    
    async def apply_rate_limit(self, provider_name: str):
        """Apply intelligent rate limiting"""
        if provider_name not in self.rate_limiter:
            self.rate_limiter[provider_name] = time.time()
        
        # Minimum delay between requests
        elapsed = time.time() - self.rate_limiter[provider_name]
        min_delay = 0.1  # 100ms between requests
        
        if elapsed < min_delay:
            await asyncio.sleep(min_delay - elapsed)
        
        self.rate_limiter[provider_name] = time.time()
    
    def create_decision_prompt(self, agent: AgentState, context: Dict) -> str:
        """Create contextual prompt for agent decision"""
        
        # Get recent decision patterns
        recent_decisions = agent.decision_history[-5:] if agent.decision_history else []
        
        # Social context
        social_info = ""
        if context.get('nearby_agents'):
            avg_happiness = sum(a.happiness for a in context['nearby_agents']) / len(context['nearby_agents'])
            avg_cooperation = sum(a.cooperation for a in context['nearby_agents']) / len(context['nearby_agents'])
            social_info = f"\nNearby agents avg happiness: {avg_happiness:.2f}, cooperation: {avg_cooperation:.2f}"
        
        # Learning context
        learning_info = ""
        if agent.learned_patterns:
            best_action = max(agent.learned_patterns.items(), key=lambda x: x[1])
            learning_info = f"\nPast success pattern: {best_action[0]} (success rate: {best_action[1]:.2f})"
        
        prompt = f"""
You are Agent {agent.agent_id}, a unique individual in a society simulation.

CURRENT STATE:
- Happiness: {agent.happiness:.2f}/1.0
- Wealth: ${agent.wealth:.0f}
- Energy: {agent.energy:.2f}/1.0
- Cooperation: {agent.cooperation:.2f}/1.0
- Innovation: {agent.innovation:.2f}/1.0
- Reputation: {agent.reputation:.2f}/1.0

PERSONALITY:
- Risk tolerance: {agent.risk_tolerance:.2f} (0=cautious, 1=bold)
- Social preference: {agent.social_preference:.2f} (0=loner, 1=social)
- Ambition: {agent.ambition:.2f} (0=content, 1=driven)

{social_info}
{learning_info}

RECENT DECISIONS: {[d.get('action', 'NONE') for d in recent_decisions]}

AVAILABLE ACTIONS:
1. WORK - Earn money, may reduce happiness/energy
2. SOCIALIZE - Build relationships, costs money but increases cooperation
3. INNOVATE - Create new ideas, risky but potentially rewarding
4. REST - Recover energy and happiness
5. HELP_OTHERS - Assist nearby agents, builds reputation
6. COMPETE - Challenge others, risky but can gain status

Consider your personality, current state, social context, and past experiences.
Choose the action that best fits your character and situation.

Respond with JSON: {{"action": "ACTION_NAME", "reasoning": "detailed explanation", "confidence": 0.8}}
"""
        return prompt
    
    def get_system_prompt(self, agent: AgentState) -> str:
        """Get system prompt based on agent personality"""
        
        personality_desc = ""
        if agent.risk_tolerance > 0.7:
            personality_desc += "You are bold and willing to take risks. "
        elif agent.risk_tolerance < 0.3:
            personality_desc += "You are cautious and prefer safe choices. "
        
        if agent.social_preference > 0.7:
            personality_desc += "You love social interaction and building relationships. "
        elif agent.social_preference < 0.3:
            personality_desc += "You prefer working alone and value independence. "
        
        if agent.ambition > 0.7:
            personality_desc += "You are highly ambitious and driven to succeed. "
        elif agent.ambition < 0.3:
            personality_desc += "You value contentment and work-life balance over achievement. "
        
        return f"""You are a unique AI agent with distinct personality traits in a society simulation.
{personality_desc}
Make decisions that reflect your personality while adapting to circumstances.
Always respond with valid JSON containing action, reasoning, and confidence."""
    
    def parse_ai_response(self, content: str, provider: str) -> Dict:
        """Parse AI response with fallback parsing"""
        try:
            # Try direct JSON parsing
            decision = json.loads(content)
            if 'action' in decision:
                decision['provider'] = provider
                decision['timestamp'] = datetime.now().isoformat()
                return decision
        except json.JSONDecodeError:
            pass
        
        # Fallback parsing
        content_upper = content.upper()
        actions = ['WORK', 'SOCIALIZE', 'INNOVATE', 'REST', 'HELP_OTHERS', 'COMPETE']
        
        for action in actions:
            if action in content_upper:
                return {
                    'action': action,
                    'reasoning': f'Parsed from {provider} response',
                    'confidence': 0.6,
                    'provider': f'{provider}_parsed',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Last resort
        return {
            'action': 'REST',
            'reasoning': 'Failed to parse response, defaulting to REST',
            'confidence': 0.3,
            'provider': f'{provider}_failed',
            'timestamp': datetime.now().isoformat()
        }
    
    def intelligent_fallback(self, agent: AgentState, context: Dict) -> Dict:
        """Intelligent fallback based on agent state and personality"""
        
        # Decision logic based on agent state
        if agent.energy < 0.3:
            action = 'REST'
            reasoning = 'Low energy requires rest'
        elif agent.wealth < 500 and agent.happiness > 0.4:
            action = 'WORK'
            reasoning = 'Need to earn money for survival'
        elif agent.happiness < 0.3:
            if agent.social_preference > 0.5:
                action = 'SOCIALIZE'
                reasoning = 'Social interaction needed for happiness'
            else:
                action = 'REST'
                reasoning = 'Need solitude to recover happiness'
        elif agent.ambition > 0.7 and agent.energy > 0.6:
            if agent.risk_tolerance > 0.5:
                action = 'INNOVATE'
                reasoning = 'High ambition drives innovation'
            else:
                action = 'WORK'
                reasoning = 'Ambitious but cautious approach'
        else:
            # Random choice weighted by personality
            choices = []
            if agent.social_preference > 0.5:
                choices.extend(['SOCIALIZE'] * 2)
            if agent.ambition > 0.5:
                choices.extend(['WORK', 'INNOVATE'])
            if agent.risk_tolerance > 0.5:
                choices.extend(['COMPETE', 'INNOVATE'])
            
            choices.extend(['REST', 'HELP_OTHERS'])
            action = random.choice(choices)
            reasoning = 'Personality-weighted decision'
        
        return {
            'action': action,
            'reasoning': reasoning,
            'confidence': 0.7,
            'provider': 'intelligent_fallback',
            'timestamp': datetime.now().isoformat()
        }

class DatabaseManager:
    """Manages persistent storage for agents and interactions"""
    
    def __init__(self, db_path: str = "enhanced_agents.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent1_id TEXT NOT NULL,
                    agent2_id TEXT,
                    interaction_type TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    context TEXT,
                    outcome TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    run_id TEXT PRIMARY KEY,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    total_agents INTEGER,
                    total_decisions INTEGER,
                    results TEXT
                );
            ''')
    
    def save_agent(self, agent: AgentState):
        """Save agent state to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO agents (agent_id, state, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (agent.agent_id, json.dumps(agent.to_dict())))
    
    def load_agent(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT state FROM agents WHERE agent_id = ?', 
                (agent_id,)
            )
            row = cursor.fetchone()
            if row:
                state_dict = json.loads(row[0])
                return AgentState(**state_dict)
        return None
    
    def log_interaction(self, agent1_id: str, agent2_id: str, 
                       interaction_type: str, details: Dict):
        """Log agent interaction"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO interactions (agent1_id, agent2_id, interaction_type, details)
                VALUES (?, ?, ?, ?)
            ''', (agent1_id, agent2_id, interaction_type, json.dumps(details)))
    
    def log_decision(self, agent_id: str, decision: Dict, 
                    context: Dict, outcome: Dict):
        """Log agent decision and outcome"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO decisions (agent_id, decision, context, outcome)
                VALUES (?, ?, ?, ?)
            ''', (agent_id, json.dumps(decision), json.dumps(context), json.dumps(outcome)))

class EnhancedAgentSystem:
    """Main system managing intelligent agents with interactions"""
    
    def __init__(self):
        self.api_manager = MultiProviderAPIManager()
        self.db_manager = DatabaseManager()
        self.agents: Dict[str, AgentState] = {}
        self.simulation_id = f"sim_{int(time.time())}"
        self.step_count = 0
        
    def create_agent(self, agent_id: str) -> AgentState:
        """Create a new agent with random but balanced personality"""
        
        # Generate personality that sums to reasonable ranges
        risk_tolerance = random.uniform(0.2, 0.8)
        social_preference = random.uniform(0.2, 0.8)
        ambition = random.uniform(0.3, 0.9)
        
        agent = AgentState(
            agent_id=agent_id,
            happiness=random.uniform(0.4, 0.7),
            wealth=random.uniform(800, 1200),
            cooperation=random.uniform(0.3, 0.8),
            innovation=random.uniform(0.3, 0.7),
            energy=random.uniform(0.6, 1.0),
            reputation=random.uniform(0.4, 0.6),
            risk_tolerance=risk_tolerance,
            social_preference=social_preference,
            ambition=ambition
        )
        
        self.agents[agent_id] = agent
        self.db_manager.save_agent(agent)
        return agent
    
    def get_nearby_agents(self, agent_id: str, radius: int = 5) -> List[AgentState]:
        """Get agents within interaction radius"""
        # Simple proximity based on agent ID hash for demo
        agent_hash = int(hashlib.md5(agent_id.encode()).hexdigest()[:8], 16)
        nearby = []
        
        for other_id, other_agent in self.agents.items():
            if other_id == agent_id:
                continue
            
            other_hash = int(hashlib.md5(other_id.encode()).hexdigest()[:8], 16)
            distance = abs(agent_hash - other_hash) % 1000
            
            if distance < radius * 100:
                nearby.append(other_agent)
        
        return nearby[:10]  # Limit to 10 nearby agents
    
    async def process_agent_decision(self, agent: AgentState) -> Dict:
        """Process a single agent's decision with full context"""
        
        # Get social context
        nearby_agents = self.get_nearby_agents(agent.agent_id)
        
        context = {
            'step': self.step_count,
            'nearby_agents': nearby_agents,
            'simulation_id': self.simulation_id
        }
        
        # Get AI decision
        decision = await self.api_manager.make_decision_request(agent, context)
        
        if decision:
            # Apply decision effects
            outcome = self.apply_decision_effects(agent, decision, context)
            
            # Log everything
            self.db_manager.log_decision(agent.agent_id, decision, context, outcome)
            
            # Update learned patterns
            self.update_agent_learning(agent, decision, outcome)
            
            # Process interactions
            if decision['action'] in ['SOCIALIZE', 'HELP_OTHERS', 'COMPETE']:
                await self.process_social_interactions(agent, decision, nearby_agents)
            
            # Save updated agent
            self.db_manager.save_agent(agent)
            
            return {
                'agent_id': agent.agent_id,
                'decision': decision,
                'outcome': outcome,
                'success': True
            }
        
        return {
            'agent_id': agent.agent_id,
            'decision': None,
            'outcome': None,
            'success': False
        }
    
    def apply_decision_effects(self, agent: AgentState, decision: Dict, context: Dict) -> Dict:
        """Apply decision effects with personality and context consideration"""
        
        action = decision['action']
        outcome = {'changes': {}, 'interactions': []}
        
        # Base effects modified by personality and context
        if action == 'WORK':
            wealth_gain = random.uniform(80, 220) * (1 + agent.ambition * 0.3)
            energy_cost = random.uniform(0.1, 0.2) * (2 - agent.risk_tolerance)
            happiness_change = random.uniform(-0.05, 0.02)
            
            agent.wealth += wealth_gain
            agent.energy = max(0, agent.energy - energy_cost)
            agent.happiness = max(0, min(1, agent.happiness + happiness_change))
            
            outcome['changes'] = {
                'wealth': wealth_gain,
                'energy': -energy_cost,
                'happiness': happiness_change
            }
        
        elif action == 'SOCIALIZE':
            if len(context.get('nearby_agents', [])) > 0:
                happiness_gain = random.uniform(0.05, 0.15) * agent.social_preference
                cooperation_gain = random.uniform(0.03, 0.08)
                wealth_cost = random.uniform(30, 60)
                reputation_gain = random.uniform(0.01, 0.03)
                
                agent.happiness = min(1, agent.happiness + happiness_gain)
                agent.cooperation = min(1, agent.cooperation + cooperation_gain)
                agent.wealth = max(0, agent.wealth - wealth_cost)
                agent.reputation = min(1, agent.reputation + reputation_gain)
                
                outcome['changes'] = {
                    'happiness': happiness_gain,
                    'cooperation': cooperation_gain,
                    'wealth': -wealth_cost,
                    'reputation': reputation_gain
                }
            else:
                # No one to socialize with
                outcome['changes'] = {'happiness': -0.02}
                agent.happiness = max(0, agent.happiness - 0.02)
        
        elif action == 'INNOVATE':
            success_chance = 0.3 + (agent.innovation * 0.4) + (agent.risk_tolerance * 0.2)
            
            if random.random() < success_chance:
                # Innovation success
                wealth_gain = random.uniform(100, 400)
                innovation_gain = random.uniform(0.02, 0.06)
                reputation_gain = random.uniform(0.02, 0.05)
                
                agent.wealth += wealth_gain
                agent.innovation = min(1, agent.innovation + innovation_gain)
                agent.reputation = min(1, agent.reputation + reputation_gain)
                
                outcome['changes'] = {
                    'wealth': wealth_gain,
                    'innovation': innovation_gain,
                    'reputation': reputation_gain,
                    'success': True
                }
            else:
                # Innovation failure
                wealth_loss = random.uniform(50, 150)
                energy_cost = random.uniform(0.05, 0.15)
                
                agent.wealth = max(0, agent.wealth - wealth_loss)
                agent.energy = max(0, agent.energy - energy_cost)
                
                outcome['changes'] = {
                    'wealth': -wealth_loss,
                    'energy': -energy_cost,
                    'success': False
                }
        
        elif action == 'REST':
            energy_gain = random.uniform(0.15, 0.25)
            happiness_gain = random.uniform(0.03, 0.08)
            
            agent.energy = min(1, agent.energy + energy_gain)
            agent.happiness = min(1, agent.happiness + happiness_gain)
            
            outcome['changes'] = {
                'energy': energy_gain,
                'happiness': happiness_gain
            }
        
        elif action == 'HELP_OTHERS':
            if len(context.get('nearby_agents', [])) > 0:
                reputation_gain = random.uniform(0.03, 0.08)
                cooperation_gain = random.uniform(0.02, 0.05)
                wealth_cost = random.uniform(20, 50)
                happiness_gain = random.uniform(0.02, 0.06) * agent.social_preference
                
                agent.reputation = min(1, agent.reputation + reputation_gain)
                agent.cooperation = min(1, agent.cooperation + cooperation_gain)
                agent.wealth = max(0, agent.wealth - wealth_cost)
                agent.happiness = min(1, agent.happiness + happiness_gain)
                
                outcome['changes'] = {
                    'reputation': reputation_gain,
                    'cooperation': cooperation_gain,
                    'wealth': -wealth_cost,
                    'happiness': happiness_gain
                }
        
        elif action == 'COMPETE':
            if len(context.get('nearby_agents', [])) > 0:
                success_chance = 0.4 + (agent.ambition * 0.3) + (agent.risk_tolerance * 0.2)
                
                if random.random() < success_chance:
                    # Competition success
                    wealth_gain = random.uniform(150, 300)
                    reputation_gain = random.uniform(0.03, 0.07)
                    cooperation_loss = random.uniform(0.01, 0.03)
                    
                    agent.wealth += wealth_gain
                    agent.reputation = min(1, agent.reputation + reputation_gain)
                    agent.cooperation = max(0, agent.cooperation - cooperation_loss)
                    
                    outcome['changes'] = {
                        'wealth': wealth_gain,
                        'reputation': reputation_gain,
                        'cooperation': -cooperation_loss,
                        'success': True
                    }
                else:
                    # Competition failure
                    reputation_loss = random.uniform(0.02, 0.05)
                    wealth_loss = random.uniform(50, 100)
                    
                    agent.reputation = max(0, agent.reputation - reputation_loss)
                    agent.wealth = max(0, agent.wealth - wealth_loss)
                    
                    outcome['changes'] = {
                        'reputation': -reputation_loss,
                        'wealth': -wealth_loss,
                        'success': False
                    }
        
        return outcome
    
    def update_agent_learning(self, agent: AgentState, decision: Dict, outcome: Dict):
        """Update agent's learned patterns based on decision outcomes"""
        
        action = decision['action']
        
        # Calculate success score based on outcome
        success_score = 0.5  # neutral
        
        if 'changes' in outcome:
            changes = outcome['changes']
            
            # Positive changes increase success score
            if changes.get('wealth', 0) > 0:
                success_score += 0.2
            if changes.get('happiness', 0) > 0:
                success_score += 0.2
            if changes.get('reputation', 0) > 0:
                success_score += 0.1
            if changes.get('success', False):
                success_score += 0.3
            
            # Negative changes decrease success score
            if changes.get('wealth', 0) < 0:
                success_score -= 0.1
            if changes.get('happiness', 0) < 0:
                success_score -= 0.2
            if changes.get('success', True) == False:
                success_score -= 0.2
        
        # Update learned patterns with exponential moving average
        if action in agent.learned_patterns:
            agent.learned_patterns[action] = (
                0.7 * agent.learned_patterns[action] + 
                0.3 * success_score
            )
        else:
            agent.learned_patterns[action] = success_score
    
    async def process_social_interactions(self, agent: AgentState, decision: Dict, 
                                        nearby_agents: List[AgentState]):
        """Process social interactions between agents"""
        
        if not nearby_agents:
            return
        
        action = decision['action']
        
        # Select interaction partners
        partners = random.sample(nearby_agents, min(3, len(nearby_agents)))
        
        for partner in partners:
            interaction_details = {
                'initiator_action': action,
                'partner_state': {
                    'happiness': partner.happiness,
                    'cooperation': partner.cooperation,
                    'reputation': partner.reputation
                }
            }
            
            if action == 'SOCIALIZE':
                # Mutual benefit from socializing
                if partner.social_preference > 0.5:
                    # Partner enjoys socializing
                    partner.happiness = min(1, partner.happiness + random.uniform(0.01, 0.03))
                    partner.cooperation = min(1, partner.cooperation + random.uniform(0.005, 0.015))
                    
                    # Add to social networks
                    if partner.agent_id not in agent.social_network:
                        agent.social_network.append(partner.agent_id)
                    if agent.agent_id not in partner.social_network:
                        partner.social_network.append(agent.agent_id)
                    
                    interaction_details['outcome'] = 'positive_mutual'
                else:
                    # Partner doesn't enjoy socializing much
                    interaction_details['outcome'] = 'neutral'
            
            elif action == 'HELP_OTHERS':
                # Help benefits the partner
                partner.happiness = min(1, partner.happiness + random.uniform(0.02, 0.05))
                partner.wealth += random.uniform(10, 30)
                
                # Partner may reciprocate in future
                if agent.agent_id not in partner.social_network:
                    partner.social_network.append(agent.agent_id)
                
                interaction_details['outcome'] = 'helped_partner'
            
            elif action == 'COMPETE':
                # Competition affects partner negatively
                partner.happiness = max(0, partner.happiness - random.uniform(0.01, 0.03))
                
                # May damage relationship
                if agent.agent_id in partner.social_network:
                    if random.random() < 0.3:  # 30% chance to break relationship
                        partner.social_network.remove(agent.agent_id)
                
                interaction_details['outcome'] = 'competed_against'
            
            # Log the interaction
            self.db_manager.log_interaction(
                agent.agent_id, 
                partner.agent_id, 
                action, 
                interaction_details
            )
            
            # Save updated partner
            self.db_manager.save_agent(partner)
    
    async def run_simulation_step(self) -> Dict:
        """Run one step of the simulation for all agents"""
        
        self.step_count += 1
        logger.info(f"Starting simulation step {self.step_count}")
        
        # Process all agents concurrently
        tasks = []
        for agent in self.agents.values():
            task = self.process_agent_decision(agent)
            tasks.append(task)
        
        # Execute with controlled concurrency
        results = []
        batch_size = 10  # Process 10 agents at a time
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches for rate limiting
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.5)
        
        # Analyze results
        successful_decisions = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        total_agents = len(self.agents)
        
        step_summary = {
            'step': self.step_count,
            'total_agents': total_agents,
            'successful_decisions': successful_decisions,
            'success_rate': successful_decisions / total_agents if total_agents > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Step {self.step_count} completed: {successful_decisions}/{total_agents} successful decisions")
        
        return step_summary
    
    async def run_full_simulation(self, num_agents: int = 100, num_steps: int = 10) -> Dict:
        """Run complete simulation with specified parameters"""
        
        start_time = datetime.now()
        logger.info(f"Starting simulation: {num_agents} agents, {num_steps} steps")
        
        # Create agents
        for i in range(num_agents):
            agent_id = f"agent_{i:04d}"
            self.create_agent(agent_id)
        
        logger.info(f"Created {len(self.agents)} agents")
        
        # Run simulation steps
        step_results = []
        for step in range(num_steps):
            step_result = await self.run_simulation_step()
            step_results.append(step_result)
            
            # Progress update
            logger.info(f"Completed step {step + 1}/{num_steps}")
        
        end_time = datetime.now()
        simulation_time = (end_time - start_time).total_seconds()
        
        # Calculate final statistics
        final_stats = self.calculate_simulation_statistics()
        
        simulation_results = {
            'simulation_id': self.simulation_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'simulation_time_seconds': simulation_time,
            'total_agents': num_agents,
            'total_steps': num_steps,
            'step_results': step_results,
            'final_statistics': final_stats,
            'api_usage': self.api_manager.providers
        }
        
        # Save simulation results
        with sqlite3.connect(self.db_manager.db_path) as conn:
            conn.execute('''
                INSERT INTO simulation_runs (run_id, start_time, end_time, total_agents, total_decisions, results)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.simulation_id,
                start_time.isoformat(),
                end_time.isoformat(),
                num_agents,
                sum(r['successful_decisions'] for r in step_results),
                json.dumps(simulation_results)
            ))
        
        logger.info(f"Simulation completed in {simulation_time:.1f}s")
        return simulation_results
    
    def calculate_simulation_statistics(self) -> Dict:
        """Calculate comprehensive simulation statistics"""
        
        if not self.agents:
            return {}
        
        # Basic statistics
        total_agents = len(self.agents)
        avg_happiness = sum(a.happiness for a in self.agents.values()) / total_agents
        avg_wealth = sum(a.wealth for a in self.agents.values()) / total_agents
        avg_cooperation = sum(a.cooperation for a in self.agents.values()) / total_agents
        avg_innovation = sum(a.innovation for a in self.agents.values()) / total_agents
        avg_reputation = sum(a.reputation for a in self.agents.values()) / total_agents
        avg_energy = sum(a.energy for a in self.agents.values()) / total_agents
        
        total_wealth = sum(a.wealth for a in self.agents.values())
        
        # Social network analysis
        total_connections = sum(len(a.social_network) for a in self.agents.values())
        avg_connections = total_connections / total_agents if total_agents > 0 else 0
        
        # Learning analysis
        agents_with_learning = sum(1 for a in self.agents.values() if a.learned_patterns)
        
        # Personality distribution
        personality_stats = {
            'avg_risk_tolerance': sum(a.risk_tolerance for a in self.agents.values()) / total_agents,
            'avg_social_preference': sum(a.social_preference for a in self.agents.values()) / total_agents,
            'avg_ambition': sum(a.ambition for a in self.agents.values()) / total_agents
        }
        
        return {
            'total_agents': total_agents,
            'averages': {
                'happiness': avg_happiness,
                'wealth': avg_wealth,
                'cooperation': avg_cooperation,
                'innovation': avg_innovation,
                'reputation': avg_reputation,
                'energy': avg_energy
            },
            'totals': {
                'wealth': total_wealth,
                'social_connections': total_connections
            },
            'social_metrics': {
                'avg_connections_per_agent': avg_connections,
                'agents_with_learning': agents_with_learning
            },
            'personality_distribution': personality_stats
        }

async def main():
    """Main function to run the enhanced agent system"""
    
    print("🧠 Enhanced Multi-Agent System with True AI Intelligence")
    print("=" * 60)
    
    # Initialize system
    system = EnhancedAgentSystem()
    
    # Run simulation
    results = await system.run_full_simulation(num_agents=50, num_steps=5)
    
    # Display results
    print(f"\n📊 SIMULATION RESULTS:")
    print(f"🤖 Total Agents: {results['total_agents']}")
    print(f"⏱️  Runtime: {results['simulation_time_seconds']:.1f}s")
    
    stats = results['final_statistics']
    print(f"\n📈 FINAL STATISTICS:")
    print(f"😊 Avg Happiness: {stats['averages']['happiness']:.3f}")
    print(f"💰 Total Wealth: ${stats['totals']['wealth']:,.0f}")
    print(f"🤝 Avg Cooperation: {stats['averages']['cooperation']:.3f}")
    print(f"💡 Avg Innovation: {stats['averages']['innovation']:.3f}")
    print(f"⭐ Avg Reputation: {stats['averages']['reputation']:.3f}")
    print(f"🔋 Avg Energy: {stats['averages']['energy']:.3f}")
    
    print(f"\n🌐 SOCIAL METRICS:")
    print(f"🔗 Avg Connections: {stats['social_metrics']['avg_connections_per_agent']:.1f}")
    print(f"🧠 Agents Learning: {stats['social_metrics']['agents_with_learning']}")
    
    # API usage summary
    print(f"\n🔌 API USAGE:")
    for provider, info in results['api_usage'].items():
        if info['active']:
            print(f"  {provider}: {info['calls_today']} calls")
    
    print(f"\n💾 Results saved to database: {system.db_manager.db_path}")
    print("✅ Enhanced simulation completed!")

if __name__ == "__main__":
    asyncio.run(main()) 