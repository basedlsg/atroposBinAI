#!/usr/bin/env python3
"""
STEP 1: Enhanced Agent Intelligence
==================================

Improvements over the base system:
1. Advanced personality models with behavioral patterns
2. Learning from past decisions and outcomes
3. Sophisticated fallback logic that considers context
4. Emotional state management
5. Social influence modeling
"""

import json
import random
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class EmotionalState:
    """Agent's emotional state affecting decisions"""
    stress: float = 0.5
    confidence: float = 0.5
    satisfaction: float = 0.5
    social_connection: float = 0.5
    
    def update_from_decision(self, decision: Dict, outcome: Dict):
        """Update emotional state based on decision outcomes"""
        success_rate = outcome.get('success_rate', 0.5)
        social_impact = outcome.get('social_impact', 0.0)
        
        # Confidence changes based on success
        self.confidence += (success_rate - 0.5) * 0.1
        
        # Stress changes based on risk taken vs outcome
        risk_taken = decision.get('risk_level', 0.5)
        if success_rate > 0.6:
            self.stress -= risk_taken * 0.05  # Success reduces stress
        else:
            self.stress += risk_taken * 0.1   # Failure increases stress
        
        # Social connection from interactions
        self.social_connection += social_impact * 0.05
        
        # Satisfaction from overall wellbeing
        self.satisfaction = (self.confidence * 0.4 + 
                           (1 - self.stress) * 0.3 + 
                           self.social_connection * 0.3)
        
        # Clamp values
        for attr in ['stress', 'confidence', 'satisfaction', 'social_connection']:
            setattr(self, attr, np.clip(getattr(self, attr), 0.0, 1.0))

class PersonalityProfile:
    """Advanced personality model with behavioral patterns"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        # Big Five personality traits
        self.openness = random.uniform(0.2, 0.9)
        self.conscientiousness = random.uniform(0.3, 0.9)
        self.extraversion = random.uniform(0.2, 0.8)
        self.agreeableness = random.uniform(0.3, 0.8)
        self.neuroticism = random.uniform(0.1, 0.7)
        
        # Derived behavioral tendencies
        self.risk_seeking = self.openness * 0.6 + (1 - self.neuroticism) * 0.4
        self.social_drive = self.extraversion * 0.7 + self.agreeableness * 0.3
        self.achievement_focus = self.conscientiousness * 0.8 + (1 - self.neuroticism) * 0.2
        
        # Decision patterns learned over time
        self.decision_preferences = {
            'cooperate': 0.5 + (self.agreeableness - 0.5) * 0.4,
            'compete': 0.5 + (self.extraversion - 0.5) * 0.3,
            'innovate': 0.5 + (self.openness - 0.5) * 0.4,
            'socialize': 0.5 + (self.extraversion - 0.5) * 0.5,
            'rest': 0.5 + (self.neuroticism - 0.5) * 0.3
        }
        
        # Learning parameters
        self.learning_rate = 0.1 + self.openness * 0.1
        self.memory_strength = 0.7 + self.conscientiousness * 0.3
    
    def get_decision_bias(self, action: str) -> float:
        """Get personality bias for a specific action"""
        return self.decision_preferences.get(action, 0.5)
    
    def update_preferences(self, action: str, outcome_quality: float):
        """Update decision preferences based on outcomes"""
        current_pref = self.decision_preferences.get(action, 0.5)
        
        # Reinforcement learning: good outcomes increase preference
        adjustment = (outcome_quality - 0.5) * self.learning_rate
        new_pref = current_pref + adjustment
        
        self.decision_preferences[action] = np.clip(new_pref, 0.1, 0.9)

class EnhancedIntelligence:
    """Enhanced decision-making system with learning and adaptation"""
    
    def __init__(self):
        self.personality_cache = {}
        self.decision_patterns = {}
        self.social_influence_weights = {
            'cooperation_contagion': 0.3,
            'happiness_influence': 0.2,
            'wealth_comparison': 0.15,
            'reputation_effect': 0.25
        }
    
    def get_personality(self, agent_id: str) -> PersonalityProfile:
        """Get or create personality profile for agent"""
        if agent_id not in self.personality_cache:
            self.personality_cache[agent_id] = PersonalityProfile(agent_id)
        return self.personality_cache[agent_id]
    
    def make_enhanced_decision(self, agent_state: Dict, context: Dict) -> Dict:
        """Make an intelligent decision considering personality, emotions, and context"""
        
        agent_id = agent_state['agent_id']
        personality = self.get_personality(agent_id)
        
        # Get or create emotional state
        emotional_state = self._get_emotional_state(agent_state)
        
        # Available actions with base probabilities
        actions = ['cooperate', 'compete', 'innovate', 'socialize', 'rest', 'trade']
        action_scores = {}
        
        for action in actions:
            score = self._calculate_action_score(
                action, agent_state, personality, emotional_state, context
            )
            action_scores[action] = score
        
        # Select action probabilistically based on scores
        chosen_action = self._select_action_weighted(action_scores, personality)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            chosen_action, agent_state, personality, emotional_state, context
        )
        
        # Estimate confidence
        confidence = self._calculate_confidence(
            chosen_action, action_scores, personality, emotional_state
        )
        
        return {
            'action': chosen_action,
            'reasoning': reasoning,
            'confidence': confidence,
            'personality_influence': personality.get_decision_bias(chosen_action),
            'emotional_factors': {
                'stress': emotional_state.stress,
                'confidence': emotional_state.confidence,
                'satisfaction': emotional_state.satisfaction
            },
            'decision_method': 'enhanced_intelligence',
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_action_score(self, action: str, agent_state: Dict, 
                              personality: PersonalityProfile, 
                              emotional_state: EmotionalState, 
                              context: Dict) -> float:
        """Calculate score for a specific action"""
        
        # Base personality bias
        base_score = personality.get_decision_bias(action)
        
        # Adjust for current state
        happiness = agent_state.get('happiness', 0.5)
        wealth = agent_state.get('wealth', 1000)
        energy = agent_state.get('energy', 0.5)
        cooperation = agent_state.get('cooperation', 0.5)
        
        # Action-specific adjustments
        if action == 'rest':
            # More likely when tired or stressed
            base_score += (1 - energy) * 0.3 + emotional_state.stress * 0.2
            
        elif action == 'cooperate':
            # More likely when happy and with cooperative neighbors
            base_score += happiness * 0.2 + cooperation * 0.1
            nearby_coop = self._get_nearby_cooperation(context)
            base_score += nearby_coop * 0.15
            
        elif action == 'compete':
            # More likely when confident and wealthy
            base_score += emotional_state.confidence * 0.2
            if wealth > 1200:
                base_score += 0.1
                
        elif action == 'innovate':
            # More likely when satisfied and energetic
            base_score += emotional_state.satisfaction * 0.15 + energy * 0.1
            
        elif action == 'socialize':
            # More likely when lonely or happy
            base_score += (1 - emotional_state.social_connection) * 0.2
            base_score += happiness * 0.1
            
        elif action == 'trade':
            # More likely when wealth is moderate
            wealth_factor = 1 - abs(wealth - 1000) / 1000
            base_score += wealth_factor * 0.15
        
        # Social influence from nearby agents
        social_influence = self._calculate_social_influence(action, context)
        base_score += social_influence
        
        # Learning from past experiences
        historical_success = self._get_historical_success(agent_state['agent_id'], action)
        base_score += historical_success * 0.1
        
        return np.clip(base_score, 0.0, 1.0)
    
    def _get_emotional_state(self, agent_state: Dict) -> EmotionalState:
        """Extract or create emotional state from agent data"""
        # This would be stored in the agent's learned_patterns or separate emotional state
        emotional_data = agent_state.get('learned_patterns', {}).get('emotional_state', {})
        
        return EmotionalState(
            stress=emotional_data.get('stress', 0.5),
            confidence=emotional_data.get('confidence', 0.5),
            satisfaction=emotional_data.get('satisfaction', 0.5),
            social_connection=emotional_data.get('social_connection', 0.5)
        )
    
    def _get_nearby_cooperation(self, context: Dict) -> float:
        """Calculate average cooperation of nearby agents"""
        nearby_agents = context.get('nearby_agents', [])
        if not nearby_agents:
            return 0.5
        
        total_coop = sum(agent.get('cooperation', 0.5) for agent in nearby_agents)
        return total_coop / len(nearby_agents)
    
    def _calculate_social_influence(self, action: str, context: Dict) -> float:
        """Calculate how social context influences action preference"""
        nearby_agents = context.get('nearby_agents', [])
        if not nearby_agents:
            return 0.0
        
        influence = 0.0
        
        # Recent actions of nearby agents
        recent_actions = []
        for agent in nearby_agents:
            history = agent.get('decision_history', [])
            if history:
                recent_actions.append(history[-1].get('action', ''))
        
        if recent_actions:
            action_frequency = recent_actions.count(action) / len(recent_actions)
            influence += action_frequency * 0.1  # Mild conformity effect
        
        return influence
    
    def _get_historical_success(self, agent_id: str, action: str) -> float:
        """Get historical success rate for this agent and action"""
        # This would query the database for past decision outcomes
        # For now, return neutral
        return 0.0
    
    def _select_action_weighted(self, action_scores: Dict, personality: PersonalityProfile) -> str:
        """Select action using weighted probabilities"""
        
        # Convert scores to probabilities
        total_score = sum(action_scores.values())
        if total_score == 0:
            return random.choice(list(action_scores.keys()))
        
        probabilities = {action: score/total_score for action, score in action_scores.items()}
        
        # Add some randomness based on personality
        randomness = 1 - personality.conscientiousness  # Less conscientious = more random
        if random.random() < randomness * 0.3:
            return random.choice(list(action_scores.keys()))
        
        # Weighted selection
        actions = list(probabilities.keys())
        weights = list(probabilities.values())
        
        return np.random.choice(actions, p=weights)
    
    def _generate_reasoning(self, action: str, agent_state: Dict, 
                          personality: PersonalityProfile, 
                          emotional_state: EmotionalState, 
                          context: Dict) -> str:
        """Generate human-like reasoning for the decision"""
        
        reasoning_templates = {
            'cooperate': [
                "I believe working together will benefit everyone.",
                "Cooperation has served me well in the past.",
                "I feel good when I help others succeed too."
            ],
            'compete': [
                "I'm feeling confident and ready for a challenge.",
                "Competition brings out my best performance.",
                "I need to assert myself in this situation."
            ],
            'innovate': [
                "I have an idea that could change everything.",
                "Innovation is the key to long-term success.",
                "I'm inspired to try something new today."
            ],
            'socialize': [
                "I could use some social connection right now.",
                "Building relationships is always worthwhile.",
                "I enjoy meeting and talking with others."
            ],
            'rest': [
                "I need to recharge my energy levels.",
                "Taking breaks helps me perform better later.",
                "I'm feeling a bit overwhelmed and need to pause."
            ],
            'trade': [
                "A fair exchange could benefit both parties.",
                "I see an opportunity for mutual gain.",
                "Trading resources seems like a smart move."
            ]
        }
        
        base_reasoning = random.choice(reasoning_templates.get(action, ["I think this is the right choice."]))
        
        # Add personality flavor
        if personality.neuroticism > 0.6 and emotional_state.stress > 0.6:
            base_reasoning += " Though I'm feeling a bit anxious about it."
        elif personality.extraversion > 0.7:
            base_reasoning += " I'm excited about this decision!"
        elif personality.conscientiousness > 0.7:
            base_reasoning += " I've thought this through carefully."
        
        return base_reasoning
    
    def _calculate_confidence(self, action: str, action_scores: Dict, 
                            personality: PersonalityProfile, 
                            emotional_state: EmotionalState) -> float:
        """Calculate confidence in the decision"""
        
        # Base confidence from emotional state
        base_confidence = emotional_state.confidence
        
        # Adjust based on how clear the choice was
        chosen_score = action_scores[action]
        max_score = max(action_scores.values())
        other_scores = [s for a, s in action_scores.items() if a != action]
        avg_other_score = sum(other_scores) / len(other_scores) if other_scores else 0
        
        choice_clarity = (chosen_score - avg_other_score) if avg_other_score > 0 else 0.5
        
        # Personality affects confidence
        personality_confidence = (personality.conscientiousness * 0.3 + 
                                (1 - personality.neuroticism) * 0.4 + 
                                emotional_state.satisfaction * 0.3)
        
        final_confidence = (base_confidence * 0.4 + 
                          choice_clarity * 0.3 + 
                          personality_confidence * 0.3)
        
        return np.clip(final_confidence, 0.1, 0.95)
    
    def update_from_outcome(self, agent_id: str, decision: Dict, outcome: Dict):
        """Update intelligence based on decision outcomes"""
        
        personality = self.get_personality(agent_id)
        action = decision['action']
        
        # Calculate outcome quality (0-1 scale)
        outcome_quality = self._assess_outcome_quality(outcome)
        
        # Update personality preferences
        personality.update_preferences(action, outcome_quality)
        
        # Store learning for future decisions
        if agent_id not in self.decision_patterns:
            self.decision_patterns[agent_id] = {}
        
        if action not in self.decision_patterns[agent_id]:
            self.decision_patterns[agent_id][action] = []
        
        self.decision_patterns[agent_id][action].append({
            'outcome_quality': outcome_quality,
            'context_hash': hash(str(sorted(outcome.items()))),
            'timestamp': datetime.now()
        })
        
        # Keep only recent patterns (last 50 decisions per action)
        if len(self.decision_patterns[agent_id][action]) > 50:
            self.decision_patterns[agent_id][action] = self.decision_patterns[agent_id][action][-50:]
    
    def _assess_outcome_quality(self, outcome: Dict) -> float:
        """Assess the quality of an outcome (0 = bad, 1 = excellent)"""
        
        quality_factors = []
        
        # Happiness change
        happiness_change = outcome.get('happiness_change', 0)
        quality_factors.append(0.5 + happiness_change)
        
        # Wealth change (normalized)
        wealth_change = outcome.get('wealth_change', 0)
        wealth_quality = 0.5 + np.tanh(wealth_change / 100) * 0.3  # Normalize large changes
        quality_factors.append(wealth_quality)
        
        # Energy change
        energy_change = outcome.get('energy_change', 0)
        quality_factors.append(0.5 + energy_change)
        
        # Social impact
        social_impact = outcome.get('social_impact', 0)
        quality_factors.append(0.5 + social_impact * 0.5)
        
        # Average the factors
        overall_quality = sum(quality_factors) / len(quality_factors)
        
        return np.clip(overall_quality, 0.0, 1.0)

# Test the enhanced intelligence system
if __name__ == "__main__":
    intelligence = EnhancedIntelligence()
    
    # Test agent
    test_agent = {
        'agent_id': 'test_001',
        'happiness': 0.6,
        'wealth': 1200,
        'energy': 0.4,
        'cooperation': 0.7,
        'decision_history': [],
        'learned_patterns': {}
    }
    
    # Test context
    test_context = {
        'nearby_agents': [
            {'cooperation': 0.8, 'happiness': 0.7},
            {'cooperation': 0.5, 'happiness': 0.4}
        ]
    }
    
    print("Testing Enhanced Intelligence System")
    print("=" * 40)
    
    # Make several decisions to see variety
    for i in range(5):
        decision = intelligence.make_enhanced_decision(test_agent, test_context)
        print(f"\nDecision {i+1}:")
        print(f"  Action: {decision['action']}")
        print(f"  Reasoning: {decision['reasoning']}")
        print(f"  Confidence: {decision['confidence']:.2f}")
        print(f"  Personality Influence: {decision['personality_influence']:.2f}")
        
        # Simulate outcome and learning
        fake_outcome = {
            'happiness_change': random.uniform(-0.1, 0.1),
            'wealth_change': random.uniform(-50, 100),
            'energy_change': random.uniform(-0.05, 0.05),
            'social_impact': random.uniform(-0.1, 0.1)
        }
        
        intelligence.update_from_outcome('test_001', decision, fake_outcome) 