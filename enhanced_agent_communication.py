"""
Enhanced Agent Communication System
==================================

Implements a sophisticated Pub/Sub messaging system for agent-to-agent communication,
enabling negotiation, collaboration, and complex social dynamics.

Features:
- Real-time message passing between agents
- Negotiation protocols for trading and collaboration
- Reputation-based trust system
- Message prioritization and filtering
- Conversation memory and context tracking
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Callable
from collections import defaultdict, deque
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages agents can send"""
    SOCIAL = "social"
    TRADE_OFFER = "trade_offer"
    TRADE_ACCEPT = "trade_accept"
    TRADE_REJECT = "trade_reject"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    INFORMATION_SHARE = "information_share"
    THREAT = "threat"
    ALLIANCE_REQUEST = "alliance_request"
    ALLIANCE_RESPONSE = "alliance_response"
    GOSSIP = "gossip"
    EMERGENCY = "emergency"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

@dataclass
class Message:
    """Represents a message between agents"""
    id: str
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast messages
    message_type: MessageType
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    requires_response: bool = False
    response_timeout: float = 30.0  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conversation:
    """Represents an ongoing conversation between agents"""
    id: str
    participants: Set[str]
    messages: List[Message] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    topic: Optional[str] = None
    status: str = "active"  # active, completed, abandoned

class MessageBroker:
    """Central message broker for agent communication"""
    
    def __init__(self):
        self.topics: Dict[str, List[str]] = defaultdict(list)  # topic -> subscriber_ids
        self.subscribers: Dict[str, Callable] = {}  # agent_id -> message_handler
        self.message_queue: deque = deque()
        self.conversations: Dict[str, Conversation] = {}
        self.agent_reputations: Dict[str, float] = defaultdict(lambda: 0.5)
        self.message_history: Dict[str, List[Message]] = defaultdict(list)
        self.spam_filters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
    def subscribe(self, agent_id: str, topics: List[str], handler: Callable):
        """Subscribe an agent to topics"""
        self.subscribers[agent_id] = handler
        for topic in topics:
            self.topics[topic].append(agent_id)
        logger.info(f"Agent {agent_id} subscribed to topics: {topics}")
    
    def unsubscribe(self, agent_id: str, topics: List[str]):
        """Unsubscribe an agent from topics"""
        for topic in topics:
            if agent_id in self.topics[topic]:
                self.topics[topic].remove(agent_id)
        logger.info(f"Agent {agent_id} unsubscribed from topics: {topics}")
    
    def publish(self, message: Message, topics: Optional[List[str]] = None):
        """Publish a message to topics or specific recipient"""
        if message.recipient_id:
            # Direct message
            if message.recipient_id in self.subscribers:
                self.message_queue.append((message, [message.recipient_id]))
        else:
            # Broadcast message
            target_agents = []
            if topics:
                for topic in topics:
                    target_agents.extend(self.topics[topic])
            else:
                # Broadcast to all subscribers
                target_agents = list(self.subscribers.keys())
            
            # Remove duplicates
            target_agents = list(set(target_agents))
            self.message_queue.append((message, target_agents))
        
        # Store in history
        self.message_history[message.sender_id].append(message)
        
        logger.info(f"Message {message.id} published from {message.sender_id} to {len(target_agents)} recipients")
    
    async def process_messages(self):
        """Process queued messages"""
        while self.message_queue:
            message, recipients = self.message_queue.popleft()
            
            # Check if message has expired
            if message.expires_at and time.time() > message.expires_at:
                logger.debug(f"Message {message.id} expired, skipping")
                continue
            
            # Filter recipients based on spam protection and reputation
            filtered_recipients = self._filter_recipients(message, recipients)
            
            # Deliver messages
            for recipient_id in filtered_recipients:
                if recipient_id in self.subscribers:
                    try:
                        await self.subscribers[recipient_id](message)
                    except Exception as e:
                        logger.error(f"Error delivering message to {recipient_id}: {e}")
    
    def _filter_recipients(self, message: Message, recipients: List[str]) -> List[str]:
        """Filter recipients based on spam protection and reputation"""
        filtered = []
        
        for recipient_id in recipients:
            # Skip if sender has low reputation with this recipient
            reputation_key = f"{message.sender_id}_{recipient_id}"
            if self.agent_reputations[reputation_key] < 0.2:
                continue
            
            # Skip if message is likely spam
            if self._is_spam(message, recipient_id):
                continue
            
            filtered.append(recipient_id)
        
        return filtered
    
    def _is_spam(self, message: Message, recipient_id: str) -> bool:
        """Check if message is likely spam"""
        sender_recipient_key = f"{message.sender_id}_{recipient_id}"
        recent_messages = self.spam_filters[sender_recipient_key]
        
        # Count messages in last minute
        current_time = time.time()
        recent_messages[current_time] = recent_messages.get(current_time, 0) + 1
        
        # Clean old entries
        recent_messages = {k: v for k, v in recent_messages.items() 
                          if current_time - k < 60}
        
        # Update spam filter
        self.spam_filters[sender_recipient_key] = recent_messages
        
        # Check if too many messages
        total_recent = sum(recent_messages.values())
        return total_recent > 10  # More than 10 messages per minute is spam

class NegotiationProtocol:
    """Handles negotiation between agents"""
    
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.active_negotiations: Dict[str, Dict[str, Any]] = {}
        self.negotiation_templates = self._create_templates()
    
    def _create_templates(self) -> Dict[str, Dict[str, Any]]:
        """Create negotiation templates for different scenarios"""
        return {
            "trade": {
                "min_rounds": 2,
                "max_rounds": 5,
                "timeout": 60,
                "required_fields": ["item", "quantity", "price"]
            },
            "collaboration": {
                "min_rounds": 3,
                "max_rounds": 8,
                "timeout": 120,
                "required_fields": ["project", "roles", "benefits"]
            },
            "alliance": {
                "min_rounds": 4,
                "max_rounds": 10,
                "timeout": 300,
                "required_fields": ["terms", "duration", "commitments"]
            }
        }
    
    def start_negotiation(self, negotiation_id: str, initiator_id: str, 
                         target_id: str, negotiation_type: str, 
                         initial_offer: Dict[str, Any]) -> bool:
        """Start a new negotiation"""
        if negotiation_type not in self.negotiation_templates:
            return False
        
        template = self.negotiation_templates[negotiation_type]
        
        self.active_negotiations[negotiation_id] = {
            "type": negotiation_type,
            "initiator_id": initiator_id,
            "target_id": target_id,
            "current_round": 1,
            "max_rounds": template["max_rounds"],
            "timeout": time.time() + template["timeout"],
            "offers": [initial_offer],
            "status": "active",
            "template": template
        }
        
        # Send initial offer
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=initiator_id,
            recipient_id=target_id,
            message_type=MessageType.TRADE_OFFER if negotiation_type == "trade" else MessageType.COLLABORATION_REQUEST,
            content={
                "negotiation_id": negotiation_id,
                "negotiation_type": negotiation_type,
                "offer": initial_offer,
                "round": 1
            },
            requires_response=True,
            response_timeout=template["timeout"]
        )
        
        self.broker.publish(message)
        logger.info(f"Negotiation {negotiation_id} started between {initiator_id} and {target_id}")
        return True
    
    def respond_to_negotiation(self, negotiation_id: str, responder_id: str, 
                              response: str, counter_offer: Optional[Dict[str, Any]] = None) -> bool:
        """Respond to an ongoing negotiation"""
        if negotiation_id not in self.active_negotiations:
            return False
        
        negotiation = self.active_negotiations[negotiation_id]
        
        if negotiation["status"] != "active":
            return False
        
        # Check timeout
        if time.time() > negotiation["timeout"]:
            negotiation["status"] = "timeout"
            return False
        
        # Determine message type based on response
        if response == "accept":
            negotiation["status"] = "accepted"
            message_type = MessageType.TRADE_ACCEPT if negotiation["type"] == "trade" else MessageType.COLLABORATION_RESPONSE
        elif response == "reject":
            negotiation["status"] = "rejected"
            message_type = MessageType.TRADE_REJECT if negotiation["type"] == "trade" else MessageType.COLLABORATION_RESPONSE
        else:  # counter-offer
            negotiation["current_round"] += 1
            if negotiation["current_round"] > negotiation["max_rounds"]:
                negotiation["status"] = "max_rounds_exceeded"
                return False
            
            negotiation["offers"].append(counter_offer)
            message_type = MessageType.TRADE_OFFER if negotiation["type"] == "trade" else MessageType.COLLABORATION_REQUEST
        
        # Send response
        target_id = negotiation["initiator_id"] if responder_id == negotiation["target_id"] else negotiation["target_id"]
        
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=responder_id,
            recipient_id=target_id,
            message_type=message_type,
            content={
                "negotiation_id": negotiation_id,
                "response": response,
                "counter_offer": counter_offer,
                "round": negotiation["current_round"]
            },
            requires_response=response not in ["accept", "reject"]
        )
        
        self.broker.publish(message)
        logger.info(f"Negotiation {negotiation_id} response: {response} from {responder_id}")
        return True

class EnhancedAgent:
    """Enhanced agent with sophisticated communication capabilities"""
    
    def __init__(self, agent_id: str, personality: Dict[str, float], broker: MessageBroker):
        self.agent_id = agent_id
        self.personality = personality
        self.broker = broker
        self.negotiation_protocol = NegotiationProtocol(broker)
        
        # Communication state
        self.conversations: Dict[str, Conversation] = {}
        self.message_queue: List[Message] = []
        self.relationships: Dict[str, float] = defaultdict(lambda: 0.5)
        self.trust_scores: Dict[str, float] = defaultdict(lambda: 0.5)
        self.communication_style = self._determine_communication_style()
        
        # Subscribe to relevant topics
        self._subscribe_to_topics()
    
    def _determine_communication_style(self) -> Dict[str, Any]:
        """Determine communication style based on personality"""
        return {
            "formality": self.personality.get("formality", 0.5),
            "assertiveness": self.personality.get("assertiveness", 0.5),
            "empathy": self.personality.get("empathy", 0.5),
            "persuasiveness": self.personality.get("persuasiveness", 0.5),
            "response_time": self.personality.get("response_time", 0.5)
        }
    
    def _subscribe_to_topics(self):
        """Subscribe to relevant communication topics"""
        topics = ["general", "social", "trade", "emergency"]
        
        # Add personality-based topics
        if self.personality.get("social", 0.5) > 0.7:
            topics.extend(["gossip", "alliance"])
        
        if self.personality.get("ambitious", 0.5) > 0.7:
            topics.extend(["collaboration", "information"])
        
        self.broker.subscribe(self.agent_id, topics, self._handle_message)
    
    async def _handle_message(self, message: Message):
        """Handle incoming messages"""
        # Add to queue for processing
        self.message_queue.append(message)
        
        # Update relationship with sender
        self._update_relationship(message.sender_id, message)
        
        # Process based on message type
        if message.message_type == MessageType.TRADE_OFFER:
            await self._handle_trade_offer(message)
        elif message.message_type == MessageType.COLLABORATION_REQUEST:
            await self._handle_collaboration_request(message)
        elif message.message_type == MessageType.ALLIANCE_REQUEST:
            await self._handle_alliance_request(message)
        elif message.message_type == MessageType.EMERGENCY:
            await self._handle_emergency(message)
        else:
            await self._handle_general_message(message)
    
    def _update_relationship(self, sender_id: str, message: Message):
        """Update relationship score with message sender"""
        base_change = 0.01
        
        # Adjust based on message type
        if message.message_type in [MessageType.THREAT, MessageType.TRADE_REJECT]:
            base_change = -0.05
        elif message.message_type in [MessageType.COLLABORATION_RESPONSE, MessageType.TRADE_ACCEPT]:
            base_change = 0.05
        
        # Adjust based on personality compatibility
        personality_compatibility = self._calculate_personality_compatibility(sender_id)
        base_change *= personality_compatibility
        
        # Update relationship
        current_relationship = self.relationships[sender_id]
        new_relationship = max(0.0, min(1.0, current_relationship + base_change))
        self.relationships[sender_id] = new_relationship
    
    def _calculate_personality_compatibility(self, other_agent_id: str) -> float:
        """Calculate personality compatibility with another agent"""
        # This would ideally use the other agent's personality
        # For now, use a simplified calculation based on own personality
        compatibility = 0.5
        
        # Adjust based on own personality traits
        if self.personality.get("social", 0.5) > 0.7:
            compatibility += 0.2
        
        if self.personality.get("trusting", 0.5) > 0.7:
            compatibility += 0.1
        
        return min(1.0, compatibility)
    
    async def _handle_trade_offer(self, message: Message):
        """Handle incoming trade offer"""
        content = message.content
        negotiation_id = content.get("negotiation_id")
        offer = content.get("offer", {})
        
        # Evaluate offer based on personality and current state
        evaluation = self._evaluate_trade_offer(offer)
        
        if evaluation["should_accept"]:
            response = "accept"
            counter_offer = None
        elif evaluation["should_counter"]:
            response = "counter"
            counter_offer = self._generate_counter_offer(offer, evaluation)
        else:
            response = "reject"
            counter_offer = None
        
        # Respond to negotiation
        self.negotiation_protocol.respond_to_negotiation(
            negotiation_id, self.agent_id, response, counter_offer
        )
    
    def _evaluate_trade_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a trade offer"""
        # Simplified evaluation logic
        # In a real implementation, this would consider:
        # - Current resources and needs
        # - Market conditions
        # - Relationship with trader
        # - Risk tolerance
        
        evaluation = {
            "should_accept": False,
            "should_counter": False,
            "confidence": 0.5
        }
        
        # Basic logic: accept if price is reasonable, counter if close, reject if too high
        price = offer.get("price", 0)
        if price < 50:  # Arbitrary threshold
            evaluation["should_accept"] = True
            evaluation["confidence"] = 0.8
        elif price < 100:
            evaluation["should_counter"] = True
            evaluation["confidence"] = 0.6
        else:
            evaluation["confidence"] = 0.9
        
        return evaluation
    
    def _generate_counter_offer(self, original_offer: Dict[str, Any], evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a counter offer"""
        # Simplified counter offer generation
        counter_offer = original_offer.copy()
        
        # Adjust price based on personality
        current_price = counter_offer.get("price", 0)
        if self.personality.get("assertiveness", 0.5) > 0.7:
            # More assertive agents try to get better deals
            counter_offer["price"] = current_price * 0.8
        else:
            # Less assertive agents make smaller adjustments
            counter_offer["price"] = current_price * 0.9
        
        return counter_offer
    
    async def _handle_collaboration_request(self, message: Message):
        """Handle collaboration request"""
        # Similar logic to trade offer handling
        content = message.content
        negotiation_id = content.get("negotiation_id")
        project = content.get("project", {})
        
        # Evaluate collaboration opportunity
        evaluation = self._evaluate_collaboration(project)
        
        if evaluation["should_accept"]:
            response = "accept"
            counter_offer = None
        elif evaluation["should_counter"]:
            response = "counter"
            counter_offer = self._generate_collaboration_counter(project, evaluation)
        else:
            response = "reject"
            counter_offer = None
        
        self.negotiation_protocol.respond_to_negotiation(
            negotiation_id, self.agent_id, response, counter_offer
        )
    
    def _evaluate_collaboration(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate collaboration opportunity"""
        evaluation = {
            "should_accept": False,
            "should_counter": False,
            "confidence": 0.5
        }
        
        # Simplified evaluation based on personality
        if self.personality.get("ambitious", 0.5) > 0.6:
            evaluation["should_accept"] = True
            evaluation["confidence"] = 0.7
        elif self.personality.get("ambitious", 0.5) > 0.4:
            evaluation["should_counter"] = True
            evaluation["confidence"] = 0.6
        
        return evaluation
    
    def _generate_collaboration_counter(self, project: Dict[str, Any], evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate collaboration counter offer"""
        counter = project.copy()
        
        # Adjust terms based on personality
        if self.personality.get("assertiveness", 0.5) > 0.7:
            counter["benefits"] = counter.get("benefits", 1.0) * 1.2
        
        return counter
    
    async def _handle_alliance_request(self, message: Message):
        """Handle alliance request"""
        # Similar to collaboration but with longer-term implications
        content = message.content
        sender_id = message.sender_id
        
        # Check relationship with sender
        relationship = self.relationships[sender_id]
        
        if relationship > 0.7:
            # Accept alliance with trusted agents
            response_message = Message(
                id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id=sender_id,
                message_type=MessageType.ALLIANCE_RESPONSE,
                content={"response": "accept", "terms": content.get("terms", {})}
            )
        else:
            # Reject alliance with less trusted agents
            response_message = Message(
                id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id=sender_id,
                message_type=MessageType.ALLIANCE_RESPONSE,
                content={"response": "reject", "reason": "insufficient_trust"}
            )
        
        self.broker.publish(response_message)
    
    async def _handle_emergency(self, message: Message):
        """Handle emergency messages"""
        # Emergency messages get highest priority
        content = message.content
        emergency_type = content.get("type", "unknown")
        
        # Respond based on personality and emergency type
        if self.personality.get("helpful", 0.5) > 0.6:
            # Helpful agents respond to emergencies
            response_message = Message(
                id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                message_type=MessageType.INFORMATION_SHARE,
                content={"response": "assistance_offered", "capabilities": self._get_capabilities()},
                priority=MessagePriority.HIGH
            )
            self.broker.publish(response_message)
    
    def _get_capabilities(self) -> List[str]:
        """Get agent capabilities for assistance"""
        capabilities = []
        
        if self.personality.get("intelligent", 0.5) > 0.6:
            capabilities.append("problem_solving")
        
        if self.personality.get("strong", 0.5) > 0.6:
            capabilities.append("physical_assistance")
        
        if self.personality.get("wealthy", 0.5) > 0.6:
            capabilities.append("financial_support")
        
        return capabilities
    
    async def _handle_general_message(self, message: Message):
        """Handle general messages"""
        # Store in conversation history
        conversation_id = self._get_conversation_id(message.sender_id)
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                id=conversation_id,
                participants={self.agent_id, message.sender_id}
            )
        
        self.conversations[conversation_id].messages.append(message)
        self.conversations[conversation_id].last_activity = time.time()
    
    def _get_conversation_id(self, other_agent_id: str) -> str:
        """Get conversation ID for two agents"""
        # Create consistent conversation ID
        participants = sorted([self.agent_id, other_agent_id])
        return f"conv_{participants[0]}_{participants[1]}"
    
    async def send_message(self, recipient_id: str, message_type: MessageType, 
                          content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL):
        """Send a message to another agent"""
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        self.broker.publish(message)
    
    async def broadcast_message(self, message_type: MessageType, content: Dict[str, Any], 
                               topics: List[str], priority: MessagePriority = MessagePriority.NORMAL):
        """Broadcast a message to multiple agents"""
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            recipient_id=None,  # None for broadcast
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        self.broker.publish(message, topics)
    
    def start_trade_negotiation(self, target_id: str, item: str, quantity: int, price: float) -> str:
        """Start a trade negotiation"""
        negotiation_id = str(uuid.uuid4())
        
        initial_offer = {
            "item": item,
            "quantity": quantity,
            "price": price
        }
        
        success = self.negotiation_protocol.start_negotiation(
            negotiation_id, self.agent_id, target_id, "trade", initial_offer
        )
        
        return negotiation_id if success else None
    
    def start_collaboration_negotiation(self, target_id: str, project: Dict[str, Any]) -> str:
        """Start a collaboration negotiation"""
        negotiation_id = str(uuid.uuid4())
        
        success = self.negotiation_protocol.start_negotiation(
            negotiation_id, self.agent_id, target_id, "collaboration", project
        )
        
        return negotiation_id if success else None

class EnhancedSocietySimulator:
    """Enhanced society simulator with sophisticated agent communication"""
    
    def __init__(self, num_agents: int = 100):
        self.num_agents = num_agents
        self.broker = MessageBroker()
        self.agents: Dict[str, EnhancedAgent] = {}
        self.simulation_time = 0
        self.metrics = {
            "messages_sent": 0,
            "negotiations_started": 0,
            "negotiations_completed": 0,
            "relationships_formed": 0,
            "alliances_created": 0
        }
        
        self._create_agents()
    
    def _create_agents(self):
        """Create agents with diverse personalities"""
        for i in range(self.num_agents):
            agent_id = f"agent_{i:04d}"
            
            # Generate diverse personality
            personality = {
                "social": self._random_trait(),
                "ambitious": self._random_trait(),
                "trusting": self._random_trait(),
                "assertive": self._random_trait(),
                "intelligent": self._random_trait(),
                "helpful": self._random_trait(),
                "formality": self._random_trait(),
                "empathy": self._random_trait(),
                "persuasiveness": self._random_trait(),
                "response_time": self._random_trait()
            }
            
            agent = EnhancedAgent(agent_id, personality, self.broker)
            self.agents[agent_id] = agent
    
    def _random_trait(self) -> float:
        """Generate a random personality trait"""
        import random
        return random.uniform(0.0, 1.0)
    
    async def run_simulation(self, steps: int = 100):
        """Run the enhanced society simulation"""
        logger.info(f"Starting enhanced society simulation with {self.num_agents} agents")
        
        for step in range(steps):
            self.simulation_time = step
            
            # Process messages
            await self.broker.process_messages()
            
            # Generate agent interactions
            await self._generate_interactions()
            
            # Update metrics
            self._update_metrics()
            
            # Log progress
            if step % 10 == 0:
                logger.info(f"Step {step}: {self.metrics['messages_sent']} messages sent, "
                           f"{self.metrics['negotiations_completed']} negotiations completed")
        
        logger.info("Enhanced society simulation completed")
        return self._generate_final_report()
    
    async def _generate_interactions(self):
        """Generate random interactions between agents"""
        import random
        
        # Select random agents for interactions
        num_interactions = max(1, self.num_agents // 10)  # 10% of agents interact per step
        
        for _ in range(num_interactions):
            agent1_id = random.choice(list(self.agents.keys()))
            agent2_id = random.choice(list(self.agents.keys()))
            
            if agent1_id == agent2_id:
                continue
            
            agent1 = self.agents[agent1_id]
            agent2 = self.agents[agent2_id]
            
            # Determine interaction type based on personalities
            interaction_type = self._determine_interaction_type(agent1, agent2)
            
            if interaction_type == "trade":
                await self._initiate_trade(agent1, agent2)
            elif interaction_type == "collaboration":
                await self._initiate_collaboration(agent1, agent2)
            elif interaction_type == "social":
                await self._initiate_social_interaction(agent1, agent2)
            elif interaction_type == "alliance":
                await self._initiate_alliance(agent1, agent2)
    
    def _determine_interaction_type(self, agent1: EnhancedAgent, agent2: EnhancedAgent) -> str:
        """Determine the type of interaction between two agents"""
        import random
        
        # Check relationship
        relationship = agent1.relationships[agent2.agent_id]
        
        if relationship > 0.8:
            # High relationship: likely collaboration or alliance
            if agent1.personality.get("ambitious", 0.5) > 0.6:
                return "collaboration"
            else:
                return "alliance"
        elif relationship > 0.5:
            # Medium relationship: likely trade or social
            if agent1.personality.get("social", 0.5) > 0.6:
                return "social"
            else:
                return "trade"
        else:
            # Low relationship: likely trade or social
            return random.choice(["trade", "social"])
    
    async def _initiate_trade(self, agent1: EnhancedAgent, agent2: EnhancedAgent):
        """Initiate a trade between agents"""
        import random
        
        # Generate trade parameters
        items = ["food", "tools", "knowledge", "services", "materials"]
        item = random.choice(items)
        quantity = random.randint(1, 10)
        price = random.uniform(10, 100)
        
        # Start negotiation
        negotiation_id = agent1.start_trade_negotiation(agent2.agent_id, item, quantity, price)
        
        if negotiation_id:
            self.metrics["negotiations_started"] += 1
    
    async def _initiate_collaboration(self, agent1: EnhancedAgent, agent2: EnhancedAgent):
        """Initiate collaboration between agents"""
        import random
        
        projects = [
            {"name": "Research Project", "duration": 30, "benefits": 0.8},
            {"name": "Infrastructure Build", "duration": 60, "benefits": 0.9},
            {"name": "Knowledge Exchange", "duration": 15, "benefits": 0.7}
        ]
        
        project = random.choice(projects).copy()
        project["roles"] = {"agent1": "coordinator", "agent2": "contributor"}
        
        # Start negotiation
        negotiation_id = agent1.start_collaboration_negotiation(agent2.agent_id, project)
        
        if negotiation_id:
            self.metrics["negotiations_started"] += 1
    
    async def _initiate_social_interaction(self, agent1: EnhancedAgent, agent2: EnhancedAgent):
        """Initiate social interaction between agents"""
        # Send social message
        await agent1.send_message(
            agent2.agent_id,
            MessageType.SOCIAL,
            {"greeting": "Hello!", "topic": "general_conversation"}
        )
        
        self.metrics["messages_sent"] += 1
    
    async def _initiate_alliance(self, agent1: EnhancedAgent, agent2: EnhancedAgent):
        """Initiate alliance request between agents"""
        await agent1.send_message(
            agent2.agent_id,
            MessageType.ALLIANCE_REQUEST,
            {
                "terms": {"duration": 100, "commitments": ["mutual_support", "information_sharing"]},
                "benefits": {"security": 0.8, "efficiency": 0.7}
            }
        )
        
        self.metrics["messages_sent"] += 1
    
    def _update_metrics(self):
        """Update simulation metrics"""
        # Count completed negotiations
        completed_negotiations = sum(
            1 for negotiation in self.broker.negotiation_protocol.active_negotiations.values()
            if negotiation["status"] in ["accepted", "rejected", "timeout"]
        )
        
        self.metrics["negotiations_completed"] = completed_negotiations
        
        # Count relationships above threshold
        total_relationships = 0
        for agent in self.agents.values():
            strong_relationships = sum(1 for rel in agent.relationships.values() if rel > 0.7)
            total_relationships += strong_relationships
        
        self.metrics["relationships_formed"] = total_relationships // 2  # Divide by 2 since each relationship is counted twice
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final simulation report"""
        return {
            "simulation_parameters": {
                "num_agents": self.num_agents,
                "simulation_steps": self.simulation_time,
                "total_messages": self.metrics["messages_sent"]
            },
            "communication_metrics": {
                "negotiations_started": self.metrics["negotiations_started"],
                "negotiations_completed": self.metrics["negotiations_completed"],
                "success_rate": (self.metrics["negotiations_completed"] / 
                               max(1, self.metrics["negotiations_started"])) * 100,
                "relationships_formed": self.metrics["relationships_formed"],
                "alliances_created": self.metrics["alliances_created"]
            },
            "agent_statistics": {
                "total_conversations": sum(len(agent.conversations) for agent in self.agents.values()),
                "average_relationships": sum(
                    sum(agent.relationships.values()) for agent in self.agents.values()
                ) / (len(self.agents) * len(self.agents)),
                "message_distribution": self._analyze_message_distribution()
            },
            "personality_analysis": self._analyze_personality_impact()
        }
    
    def _analyze_message_distribution(self) -> Dict[str, int]:
        """Analyze distribution of message types"""
        distribution = defaultdict(int)
        
        for agent in self.agents.values():
            for message in agent.message_queue:
                distribution[message.message_type.value] += 1
        
        return dict(distribution)
    
    def _analyze_personality_impact(self) -> Dict[str, Any]:
        """Analyze impact of personality on communication"""
        analysis = {
            "social_agents": {"count": 0, "avg_messages": 0},
            "ambitious_agents": {"count": 0, "avg_messages": 0},
            "trusting_agents": {"count": 0, "avg_messages": 0}
        }
        
        for agent in self.agents.values():
            if agent.personality.get("social", 0.5) > 0.7:
                analysis["social_agents"]["count"] += 1
                analysis["social_agents"]["avg_messages"] += len(agent.message_queue)
            
            if agent.personality.get("ambitious", 0.5) > 0.7:
                analysis["ambitious_agents"]["count"] += 1
                analysis["ambitious_agents"]["avg_messages"] += len(agent.message_queue)
            
            if agent.personality.get("trusting", 0.5) > 0.7:
                analysis["trusting_agents"]["count"] += 1
                analysis["trusting_agents"]["avg_messages"] += len(agent.message_queue)
        
        # Calculate averages
        for category in analysis.values():
            if category["count"] > 0:
                category["avg_messages"] /= category["count"]
        
        return analysis

async def main():
    """Main function to run the enhanced agent communication system"""
    print("🚀 Enhanced Agent Communication System")
    print("=" * 50)
    
    # Create and run simulation
    simulator = EnhancedSocietySimulator(num_agents=50)
    results = await simulator.run_simulation(steps=50)
    
    # Print results
    print("\n📊 Simulation Results:")
    print(f"Agents: {results['simulation_parameters']['num_agents']}")
    print(f"Steps: {results['simulation_parameters']['simulation_steps']}")
    print(f"Total Messages: {results['simulation_parameters']['total_messages']}")
    print(f"Negotiations: {results['communication_metrics']['negotiations_started']} started, "
          f"{results['communication_metrics']['negotiations_completed']} completed")
    print(f"Success Rate: {results['communication_metrics']['success_rate']:.1f}%")
    print(f"Relationships Formed: {results['communication_metrics']['relationships_formed']}")
    
    print("\n📈 Message Distribution:")
    for msg_type, count in results['agent_statistics']['message_distribution'].items():
        print(f"  {msg_type}: {count}")
    
    print("\n🧠 Personality Impact:")
    for personality, stats in results['personality_analysis'].items():
        print(f"  {personality}: {stats['count']} agents, {stats['avg_messages']:.1f} avg messages")
    
    return results

if __name__ == "__main__":
    asyncio.run(main()) 