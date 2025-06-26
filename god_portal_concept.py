#!/usr/bin/env python3
"""
God Portal - AI Observer for 2,500-Agent Society
Real-time narrative generation and multi-scale analysis of emergent behaviors
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Import our verified Groq integration
from llm_integration import LLMManager, LLMProvider, LLMRequest

class ObservationScale(Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    SOCIETY = "society"
    META = "meta"

class EventType(Enum):
    SOCIAL = "social"
    ECONOMIC = "economic"
    CULTURAL = "cultural"
    INNOVATION = "innovation"
    CONFLICT = "conflict"
    COOPERATION = "cooperation"

@dataclass
class SocietyObservation:
    timestamp: str
    scale: ObservationScale
    event_type: EventType
    participants: List[str]
    description: str
    significance: float
    data_snapshot: Dict[str, Any]

@dataclass
class NarrativeInsight:
    timestamp: str
    narrative: str
    key_agents: List[str]
    trends_identified: List[str]
    predictions: List[str]
    research_opportunities: List[str]

class GodPortalAI:
    """
    AI Observer that watches the 2,500-agent society and generates
    real-time narratives, insights, and research opportunities
    """
    
    def __init__(self):
        # Use our verified Groq integration
        self.llm_manager = LLMManager(provider=LLMProvider.GROQ)
        
        # Observation tracking
        self.observations = []
        self.narratives = []
        self.agent_profiles = {}
        self.social_networks = {}
        self.economic_trends = {}
        
        # Analysis windows
        self.short_term_window = 50  # Last 50 steps
        self.long_term_window = 500  # Last 500 steps
        
        # Narrative generation
        self.narrative_styles = [
            "scientific_observer",
            "storyteller",
            "sociologist", 
            "economist",
            "anthropologist"
        ]
        
    async def observe_society(self, world_state: Dict[str, Any], step: int) -> SocietyObservation:
        """
        Main observation function - analyzes current world state
        and identifies significant events/patterns
        """
        
        # Extract key metrics
        agents = world_state.get('agents', [])
        interactions = world_state.get('recent_interactions', [])
        economic_data = world_state.get('economic_data', {})
        
        # Detect significant events
        significant_events = await self._detect_significant_events(
            agents, interactions, economic_data, step
        )
        
        if significant_events:
            # Choose most significant event
            primary_event = max(significant_events, key=lambda x: x.significance)
            
            # Store observation
            observation = SocietyObservation(
                timestamp=datetime.utcnow().isoformat(),
                scale=primary_event.scale,
                event_type=primary_event.event_type,
                participants=primary_event.participants,
                description=primary_event.description,
                significance=primary_event.significance,
                data_snapshot=self._create_data_snapshot(world_state)
            )
            
            self.observations.append(observation)
            return observation
            
        return None
    
    async def generate_narrative(self, 
                               recent_observations: List[SocietyObservation],
                               style: str = "scientific_observer") -> NarrativeInsight:
        """
        Generate AI narrative about recent society developments
        """
        
        # Prepare context for LLM
        context = self._prepare_narrative_context(recent_observations, style)
        
        # Create prompt based on style
        prompt = self._create_narrative_prompt(context, style)
        
        # Generate narrative using Groq Llama
        request = LLMRequest(
            agent_id="god_portal_ai",
            prompt=prompt,
            context=context,
            max_tokens=400,
            temperature=0.8
        )
        
        response = await self.llm_manager.get_response(request)
        
        if response.success:
            # Parse response for structured insights
            narrative_insight = self._parse_narrative_response(
                response.response, recent_observations
            )
            
            self.narratives.append(narrative_insight)
            return narrative_insight
        
        return None
    
    async def _detect_significant_events(self, 
                                       agents: List[Dict], 
                                       interactions: List[Dict],
                                       economic_data: Dict,
                                       step: int) -> List[SocietyObservation]:
        """
        Detect significant events in the society using pattern analysis
        """
        
        events = []
        
        # 1. Social Network Changes
        social_events = await self._analyze_social_changes(agents, interactions)
        events.extend(social_events)
        
        # 2. Economic Shifts
        economic_events = await self._analyze_economic_changes(economic_data, step)
        events.extend(economic_events)
        
        # 3. Behavioral Innovations
        innovation_events = await self._analyze_behavioral_innovations(agents)
        events.extend(innovation_events)
        
        # 4. Cultural Emergence
        cultural_events = await self._analyze_cultural_patterns(agents)
        events.extend(cultural_events)
        
        return events
    
    async def _analyze_social_changes(self, 
                                    agents: List[Dict], 
                                    interactions: List[Dict]) -> List[SocietyObservation]:
        """Analyze social network formation and changes"""
        
        events = []
        
        # Detect new social clusters
        current_connections = self._extract_social_connections(interactions)
        
        if hasattr(self, 'previous_connections'):
            new_clusters = self._detect_new_social_clusters(
                current_connections, self.previous_connections
            )
            
            for cluster in new_clusters:
                if len(cluster) >= 5:  # Significant cluster
                    events.append(SocietyObservation(
                        timestamp=datetime.utcnow().isoformat(),
                        scale=ObservationScale.GROUP,
                        event_type=EventType.SOCIAL,
                        participants=[str(agent_id) for agent_id in cluster],
                        description=f"New social cluster formed with {len(cluster)} members",
                        significance=len(cluster) / 10.0,  # Significance based on size
                        data_snapshot={"cluster_members": cluster}
                    ))
        
        self.previous_connections = current_connections
        return events
    
    async def _analyze_economic_changes(self, 
                                      economic_data: Dict, 
                                      step: int) -> List[SocietyObservation]:
        """Analyze economic trends and disruptions"""
        
        events = []
        
        # Track wealth distribution changes
        current_wealth = economic_data.get('wealth_distribution', {})
        
        if step in self.economic_trends:
            previous_wealth = self.economic_trends[step - 10].get('wealth_distribution', {})
            
            # Calculate Gini coefficient change
            gini_change = self._calculate_gini_change(current_wealth, previous_wealth)
            
            if abs(gini_change) > 0.05:  # Significant inequality change
                event_type = EventType.ECONOMIC
                description = f"Wealth inequality {'increased' if gini_change > 0 else 'decreased'} by {abs(gini_change):.3f}"
                
                events.append(SocietyObservation(
                    timestamp=datetime.utcnow().isoformat(),
                    scale=ObservationScale.SOCIETY,
                    event_type=event_type,
                    participants=["society"],
                    description=description,
                    significance=abs(gini_change) * 10,
                    data_snapshot={"gini_change": gini_change, "wealth_data": current_wealth}
                ))
        
        self.economic_trends[step] = economic_data
        return events
    
    def _create_narrative_prompt(self, context: Dict[str, Any], style: str) -> str:
        """Create LLM prompt for narrative generation"""
        
        recent_events = context.get('recent_events', [])
        trends = context.get('trends', [])
        key_agents = context.get('key_agents', [])
        
        if style == "scientific_observer":
            prompt = f"""You are an AI scientist observing a society of 2,500 autonomous agents. 
            
Recent significant events:
{chr(10).join(f"- {event}" for event in recent_events[:5])}

Observed trends:
{chr(10).join(f"- {trend}" for trend in trends[:3])}

Key agents involved: {', '.join(key_agents[:5])}

Write a scientific observation report (2-3 paragraphs) analyzing:
1. What patterns are emerging in this society?
2. What behavioral innovations are you observing?
3. What research questions does this raise?
4. What do you predict will happen next?

Write as an objective scientific observer studying emergent AI behavior."""

        elif style == "storyteller":
            prompt = f"""You are a storyteller watching a living society of 2,500 AI beings unfold.

Recent events in this world:
{chr(10).join(f"- {event}" for event in recent_events[:5])}

Notable characters: {', '.join(key_agents[:5])}

Tell the story of what's happening in this society (2-3 paragraphs). Focus on:
1. The drama and relationships between agents
2. Conflicts and cooperations emerging
3. How individual decisions are shaping the whole society
4. What might happen next in this unfolding story

Write as a narrator observing a living, breathing world."""

        elif style == "sociologist":
            prompt = f"""You are a sociologist studying emergent social structures in a 2,500-agent AI society.

Social phenomena observed:
{chr(10).join(f"- {event}" for event in recent_events[:5])}

Current social trends:
{chr(10).join(f"- {trend}" for trend in trends[:3])}

Analyze the social dynamics (2-3 paragraphs):
1. What social structures are forming?
2. How are cultural norms emerging?
3. What social innovations are appearing?
4. What implications does this have for understanding human societies?

Write as a social scientist making discoveries."""

        else:  # Default to scientific_observer
            prompt = self._create_narrative_prompt(context, "scientific_observer")
            
        return prompt
    
    def _parse_narrative_response(self, 
                                response: str, 
                                observations: List[SocietyObservation]) -> NarrativeInsight:
        """Parse LLM response into structured insight"""
        
        # Extract key agents mentioned
        key_agents = []
        for obs in observations[-5:]:  # Last 5 observations
            key_agents.extend(obs.participants)
        key_agents = list(set(key_agents))[:10]  # Top 10 unique agents
        
        # Extract trends (simple keyword analysis)
        trends_identified = []
        trend_keywords = ["forming", "emerging", "increasing", "decreasing", "developing"]
        for keyword in trend_keywords:
            if keyword in response.lower():
                # Extract sentence containing the keyword
                sentences = response.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        trends_identified.append(sentence.strip())
                        break
        
        # Extract predictions (look for future tense)
        predictions = []
        prediction_keywords = ["will", "likely", "expect", "predict", "next"]
        for keyword in prediction_keywords:
            if keyword in response.lower():
                sentences = response.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        predictions.append(sentence.strip())
                        break
        
        # Extract research opportunities
        research_opportunities = []
        if "research" in response.lower() or "study" in response.lower():
            research_opportunities.append("Emergent behavior analysis opportunity identified")
        if "innovation" in response.lower():
            research_opportunities.append("Behavioral innovation research potential")
        if "social" in response.lower() and "structure" in response.lower():
            research_opportunities.append("Social structure formation study")
        
        return NarrativeInsight(
            timestamp=datetime.utcnow().isoformat(),
            narrative=response.strip(),
            key_agents=key_agents,
            trends_identified=trends_identified[:5],
            predictions=predictions[:3],
            research_opportunities=research_opportunities[:3]
        )
    
    def _prepare_narrative_context(self, 
                                 observations: List[SocietyObservation],
                                 style: str) -> Dict[str, Any]:
        """Prepare context for narrative generation"""
        
        recent_events = []
        trends = []
        key_agents = set()
        
        # Analyze recent observations
        for obs in observations[-10:]:  # Last 10 observations
            recent_events.append(obs.description)
            key_agents.update(obs.participants)
            
            # Extract trends based on event types
            if obs.event_type == EventType.SOCIAL:
                trends.append("Social network evolution")
            elif obs.event_type == EventType.ECONOMIC:
                trends.append("Economic restructuring")
            elif obs.event_type == EventType.INNOVATION:
                trends.append("Behavioral innovation")
        
        return {
            'recent_events': recent_events,
            'trends': list(set(trends)),
            'key_agents': list(key_agents)[:10],
            'observation_count': len(observations),
            'style': style
        }
    
    def _extract_social_connections(self, interactions: List[Dict]) -> Dict[str, List[str]]:
        """Extract social network from interactions"""
        connections = {}
        
        for interaction in interactions:
            agent1 = str(interaction.get('agent1_id', ''))
            agent2 = str(interaction.get('agent2_id', ''))
            
            if agent1 and agent2:
                if agent1 not in connections:
                    connections[agent1] = []
                if agent2 not in connections:
                    connections[agent2] = []
                
                connections[agent1].append(agent2)
                connections[agent2].append(agent1)
        
        return connections
    
    def _detect_new_social_clusters(self, 
                                  current: Dict[str, List[str]], 
                                  previous: Dict[str, List[str]]) -> List[List[str]]:
        """Detect newly formed social clusters"""
        # Simplified cluster detection - in production would use graph algorithms
        new_clusters = []
        
        # Find agents with significantly more connections
        for agent_id, connections in current.items():
            prev_connections = previous.get(agent_id, [])
            
            if len(connections) > len(prev_connections) + 3:  # Significant increase
                # This agent is part of a new cluster
                cluster = [agent_id] + connections[-5:]  # Include recent connections
                new_clusters.append(cluster)
        
        return new_clusters
    
    def _calculate_gini_change(self, current: Dict, previous: Dict) -> float:
        """Calculate change in Gini coefficient (wealth inequality)"""
        # Simplified Gini calculation
        if not current or not previous:
            return 0.0
        
        # Extract wealth values
        current_wealth = list(current.values()) if current else [0]
        previous_wealth = list(previous.values()) if previous else [0]
        
        # Simple inequality measure (would use proper Gini in production)
        current_std = np.std(current_wealth) if len(current_wealth) > 1 else 0
        previous_std = np.std(previous_wealth) if len(previous_wealth) > 1 else 0
        
        return (current_std - previous_std) / (previous_std + 1e-6)
    
    def _create_data_snapshot(self, world_state: Dict[str, Any]) -> Dict[str, Any]:
        """Create compressed data snapshot for observation"""
        return {
            'agent_count': len(world_state.get('agents', [])),
            'interaction_count': len(world_state.get('recent_interactions', [])),
            'avg_energy': np.mean([a.get('energy', 0) for a in world_state.get('agents', [])]),
            'avg_happiness': np.mean([a.get('happiness', 0) for a in world_state.get('agents', [])]),
            'total_currency': sum([a.get('currency', 0) for a in world_state.get('agents', [])]),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _analyze_behavioral_innovations(self, agents: List[Dict]) -> List[SocietyObservation]:
        """Detect behavioral innovations and adaptations"""
        # Placeholder for innovation detection
        return []
    
    async def _analyze_cultural_patterns(self, agents: List[Dict]) -> List[SocietyObservation]:
        """Detect emerging cultural patterns"""
        # Placeholder for cultural analysis
        return []

class GodPortalDashboard:
    """
    Real-time dashboard for the God Portal
    Shows live narratives, insights, and society evolution
    """
    
    def __init__(self, god_portal: GodPortalAI):
        self.god_portal = god_portal
        self.live_narratives = []
        self.research_insights = []
    
    async def run_live_observation(self, simulation_data_stream):
        """
        Run continuous observation of the society simulation
        """
        
        print("🔮 God Portal: Beginning observation of 2,500-agent society...")
        print("=" * 60)
        
        step = 0
        narrative_counter = 0
        
        async for world_state in simulation_data_stream:
            step += 1
            
            # Observe current state
            observation = await self.god_portal.observe_society(world_state, step)
            
            if observation:
                print(f"\n📊 Step {step} - {observation.event_type.value.title()} Event Detected")
                print(f"   Scale: {observation.scale.value}")
                print(f"   Significance: {observation.significance:.2f}")
                print(f"   Description: {observation.description}")
            
            # Generate narrative every 25 steps
            if step % 25 == 0 and len(self.god_portal.observations) >= 5:
                narrative_counter += 1
                
                print(f"\n🤖 Generating AI Narrative #{narrative_counter}...")
                
                # Cycle through different narrative styles
                styles = ["scientific_observer", "storyteller", "sociologist"]
                style = styles[narrative_counter % len(styles)]
                
                narrative = await self.god_portal.generate_narrative(
                    self.god_portal.observations[-10:], style
                )
                
                if narrative:
                    print(f"\n📖 {style.replace('_', ' ').title()} Perspective:")
                    print("-" * 50)
                    print(narrative.narrative)
                    
                    if narrative.trends_identified:
                        print(f"\n📈 Trends Identified:")
                        for trend in narrative.trends_identified:
                            print(f"   • {trend}")
                    
                    if narrative.predictions:
                        print(f"\n🔮 Predictions:")
                        for prediction in narrative.predictions:
                            print(f"   • {prediction}")
                    
                    if narrative.research_opportunities:
                        print(f"\n🔬 Research Opportunities:")
                        for opportunity in narrative.research_opportunities:
                            print(f"   • {opportunity}")
                    
                    self.live_narratives.append(narrative)
            
            # Brief pause for readability
            await asyncio.sleep(0.1)

async def demo_god_portal():
    """
    Demo the God Portal concept with simulated society data
    """
    
    print("🌟 GOD PORTAL DEMO")
    print("=" * 60)
    print("Watching a simulated 2,500-agent society with AI observer...")
    print()
    
    # Initialize God Portal
    god_portal = GodPortalAI()
    dashboard = GodPortalDashboard(god_portal)
    
    # Simulate society data stream
    async def simulate_society_stream():
        for step in range(100):
            # Generate mock world state
            world_state = {
                'agents': [
                    {
                        'id': i,
                        'energy': np.random.uniform(0.3, 1.0),
                        'happiness': np.random.uniform(0.2, 0.9),
                        'currency': np.random.randint(50, 500),
                        'agent_type': np.random.choice(['trader', 'scholar', 'warrior', 'farmer'])
                    }
                    for i in range(100)  # Simplified for demo
                ],
                'recent_interactions': [
                    {
                        'agent1_id': np.random.randint(0, 100),
                        'agent2_id': np.random.randint(0, 100),
                        'interaction_type': np.random.choice(['trade', 'social', 'collaboration'])
                    }
                    for _ in range(20)
                ],
                'economic_data': {
                    'wealth_distribution': {
                        str(i): np.random.randint(100, 1000) 
                        for i in range(50)
                    }
                }
            }
            
            yield world_state
            await asyncio.sleep(0.5)  # Simulate real-time
    
    # Run the observation
    await dashboard.run_live_observation(simulate_society_stream())

if __name__ == "__main__":
    asyncio.run(demo_god_portal()) 