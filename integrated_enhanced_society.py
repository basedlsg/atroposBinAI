"""
Integrated Enhanced Society Simulation
=====================================

Combines the existing LLM agent system with enhanced communication capabilities,
real-time analytics, and improved features for a comprehensive agent society simulation.

Features:
- LLM-driven agent decision making (Groq API)
- Enhanced Pub/Sub communication system
- Real-time analytics and monitoring
- Negotiation and collaboration protocols
- Personality-driven behavior
- Economic and social systems
- Scalable architecture
"""

import asyncio
import json
import logging
import time
import random
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing LLM integration
try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not available. Using fallback decision system.")

@dataclass
class EnhancedAgent:
    """Enhanced agent with LLM decision making and communication capabilities"""
    
    agent_id: str
    personality: Dict[str, float]
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    health: float = 100.0
    energy: float = 100.0
    happiness: float = 50.0
    wealth: float = 100.0
    social_connections: int = 0
    actions_taken: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    last_activity: float = field(default_factory=time.time)
    status: str = "active"
    relationships: Dict[str, float] = field(default_factory=lambda: defaultdict(lambda: 0.5))
    memory: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize agent after creation"""
        # Generate random position if not provided
        if self.position == {"x": 0, "y": 0}:
            self.position = {
                "x": random.uniform(0, 100),
                "y": random.uniform(0, 100)
            }
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get current agent state for LLM decision making"""
        return {
            "agent_id": self.agent_id,
            "position": self.position,
            "health": self.health,
            "energy": self.energy,
            "happiness": self.happiness,
            "wealth": self.wealth,
            "social_connections": self.social_connections,
            "personality": self.personality,
            "relationships": dict(self.relationships),
            "recent_memory": self.memory[-5:] if self.memory else []
        }
    
    def add_memory(self, event: str, importance: float = 0.5):
        """Add an event to agent memory"""
        memory_entry = {
            "timestamp": time.time(),
            "event": event,
            "importance": importance
        }
        self.memory.append(memory_entry)
        
        # Keep only recent memories (last 50)
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]
    
    def update_relationship(self, other_agent_id: str, change: float):
        """Update relationship with another agent"""
        current = self.relationships[other_agent_id]
        self.relationships[other_agent_id] = max(0.0, min(1.0, current + change))

class LLMDecisionEngine:
    """LLM-powered decision engine for agents"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = None
        self.api_key = api_key
        
        if GROQ_AVAILABLE and api_key:
            try:
                self.client = groq.Groq(api_key=api_key)
                logger.info("LLM decision engine initialized with Groq")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
    
    async def make_decision(self, agent: EnhancedAgent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision for an agent using LLM or fallback"""
        
        if self.client:
            return await self._llm_decision(agent, context)
        else:
            return self._fallback_decision(agent, context)
    
    async def _llm_decision(self, agent: EnhancedAgent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make decision using LLM"""
        try:
            # Create prompt for decision making
            prompt = self._create_decision_prompt(agent, context)
            
            # Get LLM response
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an AI agent in a society simulation. Make decisions based on your personality, current state, and context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7 + (agent.personality.get("creativity", 0.5) * 0.3),
                max_tokens=200
            )
            
            # Parse response
            decision_text = response.choices[0].message.content
            return self._parse_llm_response(decision_text, agent)
            
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return self._fallback_decision(agent, context)
    
    def _create_decision_prompt(self, agent: EnhancedAgent, context: Dict[str, Any]) -> str:
        """Create decision prompt for LLM"""
        state = agent.get_state_summary()
        
        prompt = f"""
You are Agent {agent.agent_id} in a society simulation.

Your current state:
- Health: {state['health']:.1f}%
- Energy: {state['energy']:.1f}%
- Happiness: {state['happiness']:.1f}%
- Wealth: ${state['wealth']:.1f}
- Social connections: {state['social_connections']}
- Position: ({state['position']['x']:.1f}, {state['position']['y']:.1f})

Your personality:
- Social: {agent.personality.get('social', 0.5):.2f}
- Ambitious: {agent.personality.get('ambitious', 0.5):.2f}
- Trusting: {agent.personality.get('trusting', 0.5):.2f}
- Risk tolerance: {agent.personality.get('risk_tolerance', 0.5):.2f}

Available actions: WORK, SOCIALIZE, TRADE, INNOVATE, REST, MOVE, HELP

Context: {context.get('description', 'No specific context')}

Based on your personality and current state, choose the best action and provide reasoning.
Respond in JSON format: {{"action": "ACTION_NAME", "reasoning": "explanation", "target": "optional_target_id"}}
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str, agent: EnhancedAgent) -> Dict[str, Any]:
        """Parse LLM response into structured decision"""
        try:
            # Try to extract JSON from response
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                decision = json.loads(json_str)
            else:
                # Fallback parsing
                decision = {"action": "REST", "reasoning": "Default action", "target": None}
            
            # Validate action
            valid_actions = ["WORK", "SOCIALIZE", "TRADE", "INNOVATE", "REST", "MOVE", "HELP"]
            if decision.get("action") not in valid_actions:
                decision["action"] = "REST"
            
            return decision
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {"action": "REST", "reasoning": "Parse error", "target": None}
    
    def _fallback_decision(self, agent: EnhancedAgent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback decision system when LLM is not available"""
        state = agent.get_state_summary()
        
        # Decision logic based on personality and state
        if state['energy'] < 30:
            return {"action": "REST", "reasoning": "Low energy", "target": None}
        
        if state['wealth'] < 50 and agent.personality.get('ambitious', 0.5) > 0.6:
            return {"action": "WORK", "reasoning": "Need money", "target": None}
        
        if agent.personality.get('social', 0.5) > 0.7 and state['social_connections'] < 3:
            return {"action": "SOCIALIZE", "reasoning": "Social personality", "target": None}
        
        if agent.personality.get('risk_tolerance', 0.5) > 0.7 and state['wealth'] > 100:
            return {"action": "INNOVATE", "reasoning": "Risk-taking personality", "target": None}
        
        # Default actions based on personality
        if agent.personality.get('ambitious', 0.5) > 0.6:
            return {"action": "WORK", "reasoning": "Ambitious personality", "target": None}
        elif agent.personality.get('social', 0.5) > 0.6:
            return {"action": "SOCIALIZE", "reasoning": "Social personality", "target": None}
        else:
            return {"action": "REST", "reasoning": "Default action", "target": None}

class CommunicationSystem:
    """Enhanced communication system for agents"""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.negotiations: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def send_message(self, sender_id: str, recipient_id: str, message_type: str, content: Dict[str, Any]) -> str:
        """Send a message between agents"""
        message_id = str(uuid.uuid4())
        
        message = {
            "id": message_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message_type": message_type,
            "content": content,
            "timestamp": time.time()
        }
        
        self.messages.append(message)
        
        # Add to conversation
        conv_key = tuple(sorted([sender_id, recipient_id]))
        self.conversations[conv_key].append(message)
        
        logger.info(f"Message sent: {sender_id} -> {recipient_id} ({message_type})")
        return message_id
    
    def start_negotiation(self, initiator_id: str, target_id: str, negotiation_type: str, initial_offer: Dict[str, Any]) -> str:
        """Start a negotiation between agents"""
        negotiation_id = str(uuid.uuid4())
        
        self.negotiations[negotiation_id] = {
            "id": negotiation_id,
            "initiator_id": initiator_id,
            "target_id": target_id,
            "type": negotiation_type,
            "status": "active",
            "rounds": 1,
            "offers": [initial_offer],
            "start_time": time.time()
        }
        
        # Send initial offer
        self.send_message(initiator_id, target_id, f"{negotiation_type}_offer", {
            "negotiation_id": negotiation_id,
            "offer": initial_offer
        })
        
        logger.info(f"Negotiation started: {initiator_id} -> {target_id} ({negotiation_type})")
        return negotiation_id
    
    def respond_to_negotiation(self, negotiation_id: str, responder_id: str, response: str, counter_offer: Optional[Dict[str, Any]] = None) -> bool:
        """Respond to an ongoing negotiation"""
        if negotiation_id not in self.negotiations:
            return False
        
        negotiation = self.negotiations[negotiation_id]
        
        if negotiation["status"] != "active":
            return False
        
        # Determine target
        target_id = negotiation["initiator_id"] if responder_id == negotiation["target_id"] else negotiation["target_id"]
        
        if response == "accept":
            negotiation["status"] = "accepted"
            message_type = f"{negotiation['type']}_accept"
        elif response == "reject":
            negotiation["status"] = "rejected"
            message_type = f"{negotiation['type']}_reject"
        else:  # counter-offer
            negotiation["rounds"] += 1
            negotiation["offers"].append(counter_offer)
            message_type = f"{negotiation['type']}_counter"
        
        # Send response
        self.send_message(responder_id, target_id, message_type, {
            "negotiation_id": negotiation_id,
            "response": response,
            "counter_offer": counter_offer
        })
        
        logger.info(f"Negotiation response: {responder_id} -> {target_id} ({response})")
        return True

class EconomicSystem:
    """Economic system for the agent society"""
    
    def __init__(self):
        self.market_prices: Dict[str, float] = {
            "food": 10.0,
            "tools": 25.0,
            "knowledge": 50.0,
            "services": 30.0,
            "materials": 15.0
        }
        self.transactions: List[Dict[str, Any]] = []
        self.supply_demand: Dict[str, Dict[str, float]] = defaultdict(lambda: {"supply": 0, "demand": 0})
    
    def execute_trade(self, buyer_id: str, seller_id: str, item: str, quantity: int, price: float) -> bool:
        """Execute a trade between agents"""
        total_cost = price * quantity
        
        # Check if buyer can afford
        # This would need access to agent wealth - simplified for now
        if total_cost > 1000:  # Arbitrary limit
            return False
        
        transaction = {
            "id": str(uuid.uuid4()),
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "item": item,
            "quantity": quantity,
            "price": price,
            "total_cost": total_cost,
            "timestamp": time.time()
        }
        
        self.transactions.append(transaction)
        
        # Update market prices based on supply/demand
        self._update_market_prices(item, quantity, "demand")
        
        logger.info(f"Trade executed: {buyer_id} bought {quantity} {item} from {seller_id} for ${total_cost}")
        return True
    
    def _update_market_prices(self, item: str, quantity: int, change_type: str):
        """Update market prices based on supply/demand changes"""
        if change_type == "demand":
            self.supply_demand[item]["demand"] += quantity
        else:
            self.supply_demand[item]["supply"] += quantity
        
        # Simple price adjustment
        demand_ratio = self.supply_demand[item]["demand"] / max(1, self.supply_demand[item]["supply"])
        base_price = self.market_prices[item]
        
        # Adjust price by up to 20% based on demand/supply ratio
        price_change = (demand_ratio - 1) * 0.2
        self.market_prices[item] = base_price * (1 + price_change)

class EnhancedSocietySimulator:
    """Enhanced society simulator with LLM agents and communication"""
    
    def __init__(self, num_agents: int = 100, api_key: Optional[str] = None):
        self.num_agents = num_agents
        self.agents: Dict[str, EnhancedAgent] = {}
        self.llm_engine = LLMDecisionEngine(api_key)
        self.communication = CommunicationSystem()
        self.economy = EconomicSystem()
        self.simulation_time = 0
        self.metrics = {
            "total_actions": 0,
            "total_messages": 0,
            "total_trades": 0,
            "negotiations_started": 0,
            "negotiations_completed": 0,
            "average_happiness": 50.0,
            "average_wealth": 100.0,
            "average_energy": 100.0
        }
        
        self._create_agents()
    
    def _create_agents(self):
        """Create agents with diverse personalities"""
        for i in range(self.num_agents):
            agent_id = f"agent_{i:04d}"
            
            # Generate diverse personality
            personality = {
                "social": random.uniform(0.2, 0.9),
                "ambitious": random.uniform(0.2, 0.9),
                "trusting": random.uniform(0.2, 0.9),
                "risk_tolerance": random.uniform(0.1, 0.8),
                "creativity": random.uniform(0.2, 0.8),
                "helpful": random.uniform(0.3, 0.9)
            }
            
            agent = EnhancedAgent(agent_id, personality)
            self.agents[agent_id] = agent
    
    async def run_simulation(self, steps: int = 100):
        """Run the enhanced society simulation"""
        logger.info(f"Starting enhanced society simulation with {self.num_agents} agents")
        
        for step in range(steps):
            self.simulation_time = step
            
            # Process agent decisions
            await self._process_agent_decisions()
            
            # Process communications
            await self._process_communications()
            
            # Update metrics
            self._update_metrics()
            
            # Log progress
            if step % 10 == 0:
                logger.info(f"Step {step}: {self.metrics['total_actions']} actions, "
                           f"{self.metrics['total_messages']} messages, "
                           f"Avg happiness: {self.metrics['average_happiness']:.1f}")
        
        logger.info("Enhanced society simulation completed")
        return self._generate_final_report()
    
    async def _process_agent_decisions(self):
        """Process decisions for all agents"""
        tasks = []
        
        for agent in self.agents.values():
            if agent.status == "active":
                task = self._process_agent_decision(agent)
                tasks.append(task)
        
        # Process decisions concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_agent_decision(self, agent: EnhancedAgent):
        """Process decision for a single agent"""
        try:
            # Create context for decision
            context = self._create_decision_context(agent)
            
            # Get decision from LLM engine
            decision = await self.llm_engine.make_decision(agent, context)
            
            # Execute decision
            await self._execute_decision(agent, decision)
            
            # Update agent state
            agent.actions_taken += 1
            agent.last_activity = time.time()
            
        except Exception as e:
            logger.error(f"Error processing decision for agent {agent.agent_id}: {e}")
    
    def _create_decision_context(self, agent: EnhancedAgent) -> Dict[str, Any]:
        """Create context for agent decision making"""
        # Find nearby agents
        nearby_agents = []
        for other_agent in self.agents.values():
            if other_agent.agent_id != agent.agent_id:
                distance = self._calculate_distance(agent.position, other_agent.position)
                if distance < 20:  # Within 20 units
                    nearby_agents.append({
                        "id": other_agent.agent_id,
                        "distance": distance,
                        "relationship": agent.relationships[other_agent.agent_id]
                    })
        
        # Get market information
        market_info = {
            "prices": self.economy.market_prices.copy(),
            "recent_trades": len(self.economy.transactions[-10:]) if self.economy.transactions else 0
        }
        
        return {
            "nearby_agents": nearby_agents,
            "market_info": market_info,
            "step": self.simulation_time,
            "description": f"Step {self.simulation_time} with {len(nearby_agents)} nearby agents"
        }
    
    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate distance between two positions"""
        dx = pos1["x"] - pos2["x"]
        dy = pos1["y"] - pos2["y"]
        return (dx**2 + dy**2)**0.5
    
    async def _execute_decision(self, agent: EnhancedAgent, decision: Dict[str, Any]):
        """Execute an agent's decision"""
        action = decision.get("action", "REST")
        reasoning = decision.get("reasoning", "No reasoning provided")
        target = decision.get("target")
        
        # Add to memory
        agent.add_memory(f"Decided to {action}: {reasoning}", importance=0.7)
        
        if action == "WORK":
            await self._execute_work(agent)
        elif action == "SOCIALIZE":
            await self._execute_socialize(agent, target)
        elif action == "TRADE":
            await self._execute_trade(agent, target)
        elif action == "INNOVATE":
            await self._execute_innovate(agent)
        elif action == "REST":
            await self._execute_rest(agent)
        elif action == "MOVE":
            await self._execute_move(agent)
        elif action == "HELP":
            await self._execute_help(agent, target)
    
    async def _execute_work(self, agent: EnhancedAgent):
        """Execute work action"""
        income = random.uniform(10, 30)
        energy_cost = random.uniform(5, 15)
        
        agent.wealth += income
        agent.energy = max(0, agent.energy - energy_cost)
        agent.happiness = min(100, agent.happiness + random.uniform(-2, 2))
        
        agent.add_memory(f"Worked and earned ${income:.1f}", importance=0.6)
    
    async def _execute_socialize(self, agent: EnhancedAgent, target_id: Optional[str]):
        """Execute socialize action"""
        if target_id and target_id in self.agents:
            target = self.agents[target_id]
            
            # Calculate relationship change
            relationship_change = random.uniform(0.05, 0.15)
            agent.update_relationship(target_id, relationship_change)
            target.update_relationship(agent.agent_id, relationship_change)
            
            # Send message
            self.communication.send_message(
                agent.agent_id, target_id, "social",
                {"greeting": "Hello!", "relationship_change": relationship_change}
            )
            
            agent.social_connections += 1
            agent.happiness = min(100, agent.happiness + random.uniform(2, 8))
            agent.energy = max(0, agent.energy - random.uniform(2, 5))
            
            agent.add_memory(f"Socialized with {target_id}", importance=0.8)
        else:
            # Solo socialization
            agent.happiness = min(100, agent.happiness + random.uniform(1, 3))
            agent.energy = max(0, agent.energy - random.uniform(1, 3))
            
            agent.add_memory("Spent time alone", importance=0.3)
    
    async def _execute_trade(self, agent: EnhancedAgent, target_id: Optional[str]):
        """Execute trade action"""
        if target_id and target_id in self.agents:
            # Find an item to trade
            items = list(self.economy.market_prices.keys())
            item = random.choice(items)
            quantity = random.randint(1, 5)
            price = self.economy.market_prices[item]
            
            # Start negotiation
            negotiation_id = self.communication.start_negotiation(
                agent.agent_id, target_id, "trade",
                {"item": item, "quantity": quantity, "price": price}
            )
            
            agent.add_memory(f"Started trade negotiation for {quantity} {item}", importance=0.7)
    
    async def _execute_innovate(self, agent: EnhancedAgent):
        """Execute innovate action"""
        # Innovation has high risk/reward
        success_chance = agent.personality.get("risk_tolerance", 0.5)
        
        if random.random() < success_chance:
            # Successful innovation
            reward = random.uniform(50, 200)
            agent.wealth += reward
            agent.happiness = min(100, agent.happiness + random.uniform(5, 15))
            
            agent.add_memory(f"Successful innovation! Earned ${reward:.1f}", importance=0.9)
        else:
            # Failed innovation
            cost = random.uniform(10, 30)
            agent.wealth = max(0, agent.wealth - cost)
            agent.happiness = max(0, agent.happiness - random.uniform(2, 8))
            
            agent.add_memory(f"Failed innovation, lost ${cost:.1f}", importance=0.6)
        
        agent.energy = max(0, agent.energy - random.uniform(10, 20))
    
    async def _execute_rest(self, agent: EnhancedAgent):
        """Execute rest action"""
        energy_gain = random.uniform(10, 25)
        agent.energy = min(100, agent.energy + energy_gain)
        agent.happiness = min(100, agent.happiness + random.uniform(1, 3))
        
        agent.add_memory(f"Rested and recovered {energy_gain:.1f} energy", importance=0.4)
    
    async def _execute_move(self, agent: EnhancedAgent):
        """Execute move action"""
        # Move to random position
        new_x = max(0, min(100, agent.position["x"] + random.uniform(-10, 10)))
        new_y = max(0, min(100, agent.position["y"] + random.uniform(-10, 10)))
        
        agent.position = {"x": new_x, "y": new_y}
        agent.energy = max(0, agent.energy - random.uniform(3, 8))
        
        agent.add_memory(f"Moved to ({new_x:.1f}, {new_y:.1f})", importance=0.3)
    
    async def _execute_help(self, agent: EnhancedAgent, target_id: Optional[str]):
        """Execute help action"""
        if target_id and target_id in self.agents:
            target = self.agents[target_id]
            
            # Help another agent
            help_amount = random.uniform(5, 15)
            target.wealth += help_amount
            agent.wealth = max(0, agent.wealth - help_amount)
            
            # Improve relationship
            relationship_change = random.uniform(0.1, 0.2)
            agent.update_relationship(target_id, relationship_change)
            target.update_relationship(agent.agent_id, relationship_change)
            
            # Send help message
            self.communication.send_message(
                agent.agent_id, target_id, "help",
                {"help_amount": help_amount, "message": "I'm here to help!"}
            )
            
            agent.happiness = min(100, agent.happiness + random.uniform(3, 8))
            agent.energy = max(0, agent.energy - random.uniform(2, 5))
            
            agent.add_memory(f"Helped {target_id} with ${help_amount:.1f}", importance=0.8)
    
    async def _process_communications(self):
        """Process communications between agents"""
        # Process recent messages
        recent_messages = self.communication.messages[-50:]  # Last 50 messages
        
        for message in recent_messages:
            # Update message counts
            if message["sender_id"] in self.agents:
                self.agents[message["sender_id"]].messages_sent += 1
            
            if message["recipient_id"] in self.agents:
                self.agents[message["recipient_id"]].messages_received += 1
    
    def _update_metrics(self):
        """Update simulation metrics"""
        if not self.agents:
            return
        
        # Calculate averages
        total_happiness = sum(agent.happiness for agent in self.agents.values())
        total_wealth = sum(agent.wealth for agent in self.agents.values())
        total_energy = sum(agent.energy for agent in self.agents.values())
        total_actions = sum(agent.actions_taken for agent in self.agents.values())
        total_messages = sum(agent.messages_sent for agent in self.agents.values())
        
        num_agents = len(self.agents)
        
        self.metrics["average_happiness"] = total_happiness / num_agents
        self.metrics["average_wealth"] = total_wealth / num_agents
        self.metrics["average_energy"] = total_energy / num_agents
        self.metrics["total_actions"] = total_actions
        self.metrics["total_messages"] = total_messages
        self.metrics["total_trades"] = len(self.economy.transactions)
        self.metrics["negotiations_started"] = len(self.communication.negotiations)
        self.metrics["negotiations_completed"] = len([
            n for n in self.communication.negotiations.values() 
            if n["status"] in ["accepted", "rejected"]
        ])
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final simulation report"""
        return {
            "simulation_parameters": {
                "num_agents": self.num_agents,
                "simulation_steps": self.simulation_time,
                "llm_available": GROQ_AVAILABLE
            },
            "final_metrics": self.metrics.copy(),
            "communication_summary": {
                "total_messages": len(self.communication.messages),
                "total_negotiations": len(self.communication.negotiations),
                "successful_negotiations": len([
                    n for n in self.communication.negotiations.values() 
                    if n["status"] == "accepted"
                ]),
                "conversations": len(self.communication.conversations)
            },
            "economic_summary": {
                "total_transactions": len(self.economy.transactions),
                "market_prices": self.economy.market_prices,
                "total_volume": sum(t["total_cost"] for t in self.economy.transactions)
            },
            "agent_statistics": {
                "personality_distribution": self._analyze_personality_distribution(),
                "relationship_network": self._analyze_relationship_network(),
                "wealth_distribution": self._analyze_wealth_distribution()
            }
        }
    
    def _analyze_personality_distribution(self) -> Dict[str, Dict[str, float]]:
        """Analyze distribution of personality traits"""
        traits = ["social", "ambitious", "trusting", "risk_tolerance", "creativity", "helpful"]
        distribution = {}
        
        for trait in traits:
            values = [agent.personality.get(trait, 0.5) for agent in self.agents.values()]
            distribution[trait] = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
        
        return distribution
    
    def _analyze_relationship_network(self) -> Dict[str, Any]:
        """Analyze the relationship network"""
        total_relationships = 0
        strong_relationships = 0
        
        for agent in self.agents.values():
            for relationship in agent.relationships.values():
                total_relationships += 1
                if relationship > 0.7:
                    strong_relationships += 1
        
        return {
            "total_relationships": total_relationships,
            "strong_relationships": strong_relationships,
            "network_density": strong_relationships / max(1, total_relationships)
        }
    
    def _analyze_wealth_distribution(self) -> Dict[str, float]:
        """Analyze wealth distribution"""
        wealths = [agent.wealth for agent in self.agents.values()]
        
        return {
            "mean": sum(wealths) / len(wealths),
            "median": sorted(wealths)[len(wealths)//2],
            "min": min(wealths),
            "max": max(wealths),
            "inequality": max(wealths) / max(1, min(wealths))  # Simple inequality measure
        }

async def main():
    """Main function to run the integrated enhanced society simulation"""
    print("🚀 Integrated Enhanced Society Simulation")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️  No GROQ_API_KEY found. Using fallback decision system.")
        print("   Set GROQ_API_KEY environment variable for LLM-powered decisions.")
    
    # Create and run simulation
    simulator = EnhancedSocietySimulator(num_agents=50, api_key=api_key)
    results = await simulator.run_simulation(steps=50)
    
    # Print results
    print("\n📊 Simulation Results:")
    print(f"Agents: {results['simulation_parameters']['num_agents']}")
    print(f"Steps: {results['simulation_parameters']['simulation_steps']}")
    print(f"LLM Available: {results['simulation_parameters']['llm_available']}")
    print(f"Total Actions: {results['final_metrics']['total_actions']}")
    print(f"Total Messages: {results['final_metrics']['total_messages']}")
    print(f"Average Happiness: {results['final_metrics']['average_happiness']:.1f}")
    print(f"Average Wealth: ${results['final_metrics']['average_wealth']:.1f}")
    print(f"Average Energy: {results['final_metrics']['average_energy']:.1f}")
    
    print("\n💬 Communication Summary:")
    comm = results['communication_summary']
    print(f"Messages: {comm['total_messages']}")
    print(f"Negotiations: {comm['total_negotiations']} started, {comm['successful_negotiations']} successful")
    print(f"Conversations: {comm['conversations']}")
    
    print("\n💰 Economic Summary:")
    econ = results['economic_summary']
    print(f"Transactions: {econ['total_transactions']}")
    print(f"Total Volume: ${econ['total_volume']:.1f}")
    
    print("\n🧠 Personality Analysis:")
    for trait, stats in results['agent_statistics']['personality_distribution'].items():
        print(f"  {trait}: {stats['mean']:.2f} (range: {stats['min']:.2f}-{stats['max']:.2f})")
    
    print("\n🤝 Relationship Network:")
    network = results['agent_statistics']['relationship_network']
    print(f"  Total relationships: {network['total_relationships']}")
    print(f"  Strong relationships: {network['strong_relationships']}")
    print(f"  Network density: {network['network_density']:.3f}")
    
    print("\n💰 Wealth Distribution:")
    wealth = results['agent_statistics']['wealth_distribution']
    print(f"  Mean: ${wealth['mean']:.1f}")
    print(f"  Median: ${wealth['median']:.1f}")
    print(f"  Range: ${wealth['min']:.1f} - ${wealth['max']:.1f}")
    print(f"  Inequality ratio: {wealth['inequality']:.1f}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main()) 