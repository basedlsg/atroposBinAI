#!/usr/bin/env python3
"""
Llama API Integration Strategy
Based on comprehensive scale testing results

Key Findings:
- Llama API is working but with fallback responses (400 errors from api.llama.com)
- Performance: 7.32 RPS average, 0.128s response time
- Cost: $0.030 per 1K requests (cheapest option)
- Quality: Short responses (42 chars avg) - likely fallback responses

Strategy: Multi-provider approach with Llama optimization
"""

import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

class LlamaIntegrationStrategy:
    """
    Comprehensive strategy for integrating Llama API based on scale test results
    """
    
    def __init__(self):
        self.scale_test_results = self.load_scale_test_results()
        self.strategy = self.analyze_and_create_strategy()
    
    def load_scale_test_results(self):
        """Load the scale test results"""
        try:
            with open('scale_test_results.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def analyze_and_create_strategy(self):
        """Analyze test results and create integration strategy"""
        
        if not self.scale_test_results:
            return self.create_fallback_strategy()
        
        # Extract performance data
        results = self.scale_test_results['results']
        
        # Group by provider
        provider_stats = {}
        for result in results:
            if result['success']:
                provider = result['test_config']['provider']
                if provider not in provider_stats:
                    provider_stats[provider] = []
                provider_stats[provider].append(result['performance'])
        
        # Calculate averages
        provider_averages = {}
        for provider, stats in provider_stats.items():
            provider_averages[provider] = {
                'avg_rps': sum(s['requests_per_second'] for s in stats) / len(stats),
                'avg_response_time': sum(s['avg_response_time'] for s in stats) / len(stats),
                'success_rate': sum(s['success_rate'] for s in stats) / len(stats),
                'test_count': len(stats)
            }
        
        return self.create_strategy_from_data(provider_averages)
    
    def create_strategy_from_data(self, provider_averages):
        """Create strategy based on actual test data"""
        
        strategy = {
            'timestamp': datetime.now().isoformat(),
            'test_data_summary': provider_averages,
            'primary_findings': self.analyze_findings(provider_averages),
            'integration_approaches': self.create_integration_approaches(),
            'implementation_phases': self.create_implementation_phases(),
            'cost_optimization': self.create_cost_optimization_plan(provider_averages),
            'quality_improvement': self.create_quality_improvement_plan(),
            'fallback_strategies': self.create_fallback_strategies(),
            'monitoring_plan': self.create_monitoring_plan()
        }
        
        return strategy
    
    def analyze_findings(self, provider_averages):
        """Analyze the key findings from scale tests"""
        
        findings = {
            'llama_status': 'WORKING_WITH_ISSUES',
            'issues_identified': [
                '400 Bad Request errors from api.llama.com',
                'Falling back to rule-based responses',
                'Short response length (42 chars vs 370+ for others)',
                'No cache hits (0% vs 80-96% for others)'
            ],
            'performance_ranking': [],
            'cost_ranking': [],
            'quality_ranking': []
        }
        
        # Performance ranking
        if provider_averages:
            perf_sorted = sorted(provider_averages.items(), 
                               key=lambda x: x[1]['avg_rps'], reverse=True)
            findings['performance_ranking'] = [
                f"{provider}: {stats['avg_rps']:.2f} RPS" 
                for provider, stats in perf_sorted
            ]
        
        # Cost ranking (estimated)
        cost_per_1m = {'openai': 4.00, 'gemini': 0.50, 'llama': 0.20}
        cost_sorted = sorted(cost_per_1m.items(), key=lambda x: x[1])
        findings['cost_ranking'] = [
            f"{provider}: ${cost:.2f}/1M tokens" 
            for provider, cost in cost_sorted
        ]
        
        # Quality assessment
        findings['quality_ranking'] = [
            "Gemini: 474 chars avg, 9 strategic indicators",
            "OpenAI: 370 chars avg, 4 strategic indicators", 
            "Llama: 42 chars avg, 0 strategic indicators (FALLBACK)"
        ]
        
        return findings
    
    def create_integration_approaches(self):
        """Create different approaches for Llama integration"""
        
        return {
            'approach_1_fix_direct_api': {
                'name': 'Fix Direct Llama API',
                'description': 'Debug and fix the direct api.llama.com integration',
                'priority': 'HIGH',
                'steps': [
                    'Investigate 400 Bad Request errors',
                    'Verify API endpoint and authentication format',
                    'Test different request formats and headers',
                    'Implement proper error handling and retries'
                ],
                'pros': ['Lowest cost', 'Direct control', 'Best margins'],
                'cons': ['Unknown timeline', 'API stability concerns'],
                'estimated_effort': '2-5 days'
            },
            
            'approach_2_third_party_providers': {
                'name': 'Use Third-Party Llama Providers',
                'description': 'Integrate Llama through reliable third-party providers',
                'priority': 'MEDIUM',
                'options': [
                    {
                        'provider': 'Together AI',
                        'endpoint': 'https://api.together.xyz/v1/chat/completions',
                        'models': ['meta-llama/Llama-3.1-70B-Instruct-Turbo'],
                        'cost': '$0.88/1M tokens',
                        'reliability': 'HIGH'
                    },
                    {
                        'provider': 'Groq',
                        'endpoint': 'https://api.groq.com/openai/v1/chat/completions',
                        'models': ['llama-3.1-70b-versatile'],
                        'cost': '$0.59/1M tokens',
                        'reliability': 'HIGH',
                        'speed': 'VERY_HIGH (>100 tokens/sec)'
                    },
                    {
                        'provider': 'Replicate',
                        'endpoint': 'https://api.replicate.com/v1/predictions',
                        'models': ['meta/llama-2-70b-chat'],
                        'cost': '$0.65/1M tokens',
                        'reliability': 'MEDIUM'
                    }
                ],
                'pros': ['Proven reliability', 'Good performance', 'Multiple options'],
                'cons': ['Higher cost than direct', 'Vendor dependency'],
                'estimated_effort': '1-2 days'
            },
            
            'approach_3_self_hosted': {
                'name': 'Self-Hosted Llama',
                'description': 'Deploy Llama models on our own infrastructure',
                'priority': 'LOW',
                'options': [
                    {
                        'solution': 'vLLM on GCP',
                        'cost': '$2-4/hour GPU compute',
                        'models': ['Llama-3.1-8B', 'Llama-3.1-70B'],
                        'setup_time': '1-2 weeks'
                    },
                    {
                        'solution': 'TensorRT-LLM on GCP',
                        'cost': '$3-6/hour GPU compute',
                        'performance': 'VERY_HIGH',
                        'setup_time': '2-3 weeks'
                    }
                ],
                'pros': ['Full control', 'No API limits', 'Long-term cost savings'],
                'cons': ['High setup complexity', 'Infrastructure management'],
                'estimated_effort': '2-4 weeks'
            },
            
            'approach_4_hybrid_intelligent': {
                'name': 'Intelligent Multi-Provider System',
                'description': 'Smart routing based on task complexity and cost',
                'priority': 'HIGH',
                'routing_logic': {
                    'simple_tasks': 'Llama (cheapest)',
                    'complex_reasoning': 'OpenAI (most capable)',
                    'balanced_tasks': 'Gemini (best value)',
                    'high_volume': 'Cached responses',
                    'fallback': 'Rule-based responses'
                },
                'benefits': ['Cost optimization', 'Quality assurance', 'Reliability'],
                'estimated_effort': '3-5 days'
            }
        }
    
    def create_implementation_phases(self):
        """Create phased implementation plan"""
        
        return {
            'phase_1_immediate': {
                'timeline': '1-2 days',
                'goals': ['Get Llama working through third-party', 'Implement basic routing'],
                'tasks': [
                    'Integrate Together AI or Groq for Llama access',
                    'Add provider selection logic to LLMManager',
                    'Test with small scale simulations',
                    'Update production deployment scripts'
                ],
                'success_criteria': ['Llama responses working', '90%+ success rate', 'Cost < $1/hour']
            },
            
            'phase_2_optimization': {
                'timeline': '3-5 days',
                'goals': ['Implement intelligent routing', 'Optimize performance'],
                'tasks': [
                    'Build task complexity classifier',
                    'Implement cost-aware provider selection',
                    'Add response quality monitoring',
                    'Optimize caching strategies'
                ],
                'success_criteria': ['30% cost reduction', 'Maintained quality', 'Smart routing working']
            },
            
            'phase_3_scaling': {
                'timeline': '1-2 weeks',
                'goals': ['Scale to 1000+ agents', 'Production hardening'],
                'tasks': [
                    'Stress test with 1000+ agents',
                    'Implement rate limiting and backoff',
                    'Add comprehensive monitoring',
                    'Optimize for high-volume scenarios'
                ],
                'success_criteria': ['1000+ agent simulations', '99.9% uptime', 'Cost predictability']
            },
            
            'phase_4_advanced': {
                'timeline': '2-4 weeks',
                'goals': ['Advanced features', 'Self-hosting exploration'],
                'tasks': [
                    'Evaluate self-hosted Llama deployment',
                    'Implement advanced caching with embeddings',
                    'Add real-time cost monitoring',
                    'Build provider performance analytics'
                ],
                'success_criteria': ['Self-hosting option ready', 'Advanced analytics', 'Optimal cost/quality']
            }
        }
    
    def create_cost_optimization_plan(self, provider_averages):
        """Create cost optimization strategy"""
        
        # Calculate potential savings
        base_cost_openai = 4.00  # per 1M tokens
        base_cost_gemini = 0.50
        base_cost_llama = 0.20
        
        return {
            'current_costs': {
                'openai_only': f'${base_cost_openai:.2f}/1M tokens',
                'gemini_only': f'${base_cost_gemini:.2f}/1M tokens',
                'llama_only': f'${base_cost_llama:.2f}/1M tokens'
            },
            
            'optimization_strategies': {
                'strategy_1_provider_mix': {
                    'description': '70% Llama, 20% Gemini, 10% OpenAI',
                    'estimated_cost': f'${0.7 * base_cost_llama + 0.2 * base_cost_gemini + 0.1 * base_cost_openai:.2f}/1M tokens',
                    'savings': f'{((base_cost_openai - (0.7 * base_cost_llama + 0.2 * base_cost_gemini + 0.1 * base_cost_openai)) / base_cost_openai) * 100:.1f}%'
                },
                
                'strategy_2_intelligent_routing': {
                    'description': 'Route by complexity: Simple->Llama, Complex->Gemini/OpenAI',
                    'estimated_savings': '60-80%',
                    'quality_impact': 'Minimal (smart routing)'
                },
                
                'strategy_3_aggressive_caching': {
                    'description': 'Cache similar agent states and contexts',
                    'cache_hit_target': '95%',
                    'cost_reduction': '90%+ for repeated scenarios'
                }
            },
            
            'monthly_projections': {
                'small_scale_100_agents': {
                    'requests_per_month': 100 * 24 * 30 * 4,  # 100 agents, 24 hours, 30 days, 4 decisions/hour
                    'openai_cost': 100 * 24 * 30 * 4 * 150 / 1_000_000 * base_cost_openai,
                    'optimized_cost': 100 * 24 * 30 * 4 * 150 / 1_000_000 * 0.35,  # Mixed strategy
                    'savings': '91%'
                },
                
                'large_scale_1000_agents': {
                    'requests_per_month': 1000 * 24 * 30 * 4,
                    'openai_cost': 1000 * 24 * 30 * 4 * 150 / 1_000_000 * base_cost_openai,
                    'optimized_cost': 1000 * 24 * 30 * 4 * 150 / 1_000_000 * 0.35,
                    'savings': '91%'
                }
            }
        }
    
    def create_quality_improvement_plan(self):
        """Plan to improve Llama response quality"""
        
        return {
            'current_issues': [
                'Short responses (42 chars vs 370+ expected)',
                'No strategic thinking indicators',
                'Likely fallback responses due to API errors'
            ],
            
            'improvement_strategies': {
                'fix_api_integration': {
                    'priority': 'CRITICAL',
                    'description': 'Fix the 400 Bad Request errors',
                    'expected_impact': 'Massive - should get full Llama responses'
                },
                
                'prompt_optimization': {
                    'priority': 'HIGH',
                    'description': 'Optimize prompts specifically for Llama models',
                    'techniques': [
                        'Use Llama-specific prompt templates',
                        'Add explicit reasoning instructions',
                        'Include few-shot examples',
                        'Specify desired response length'
                    ]
                },
                
                'response_validation': {
                    'priority': 'MEDIUM',
                    'description': 'Validate response quality and retry if needed',
                    'criteria': [
                        'Minimum response length (100+ chars)',
                        'Contains agent reasoning',
                        'Matches expected format',
                        'No generic fallback phrases'
                    ]
                },
                
                'model_comparison': {
                    'priority': 'MEDIUM',
                    'description': 'Test different Llama model variants',
                    'models_to_test': [
                        'llama-3.1-8b-instruct (faster, cheaper)',
                        'llama-3.1-70b-instruct (current)',
                        'llama-3.1-405b-instruct (highest quality)'
                    ]
                }
            }
        }
    
    def create_fallback_strategies(self):
        """Create comprehensive fallback strategies"""
        
        return {
            'fallback_hierarchy': [
                '1. Primary Llama provider',
                '2. Secondary Llama provider (different endpoint)',
                '3. Gemini (balanced cost/quality)',
                '4. OpenAI (highest quality)',
                '5. Cached responses (if available)',
                '6. Rule-based responses (last resort)'
            ],
            
            'failure_scenarios': {
                'llama_api_down': {
                    'detection': 'Multiple 400/500 errors in 1 minute',
                    'action': 'Switch to Gemini for 10 minutes, then retry Llama',
                    'notification': 'Alert operations team'
                },
                
                'rate_limit_exceeded': {
                    'detection': '429 Too Many Requests',
                    'action': 'Exponential backoff + switch to backup provider',
                    'prevention': 'Implement request rate limiting'
                },
                
                'quality_degradation': {
                    'detection': 'Average response length < 50 chars for 10 requests',
                    'action': 'Switch to higher quality provider temporarily',
                    'investigation': 'Log for manual review'
                },
                
                'cost_overrun': {
                    'detection': 'Hourly cost > $10',
                    'action': 'Increase cache hit rate + reduce OpenAI usage',
                    'alert': 'Notify finance team'
                }
            }
        }
    
    def create_monitoring_plan(self):
        """Create comprehensive monitoring plan"""
        
        return {
            'key_metrics': {
                'performance': [
                    'Requests per second by provider',
                    'Average response time by provider',
                    'Success rate by provider',
                    'Cache hit rate'
                ],
                
                'quality': [
                    'Average response length',
                    'Strategic thinking indicators count',
                    'Agent decision diversity',
                    'Response coherence score'
                ],
                
                'cost': [
                    'Cost per request by provider',
                    'Daily/monthly cost trends',
                    'Cost per agent per day',
                    'Provider mix percentages'
                ],
                
                'reliability': [
                    'Error rate by provider',
                    'Failover frequency',
                    'Downtime duration',
                    'Recovery time'
                ]
            },
            
            'alerting_rules': {
                'critical': [
                    'All providers failing (>90% error rate)',
                    'Cost spike (>200% of baseline)',
                    'Response quality drop (>50% short responses)'
                ],
                
                'warning': [
                    'Single provider failing (>50% error rate)',
                    'High latency (>5s average response time)',
                    'Low cache hit rate (<70%)'
                ]
            },
            
            'dashboards': [
                'Real-time provider performance',
                'Cost tracking and projections',
                'Quality metrics and trends',
                'Agent behavior analytics'
            ]
        }
    
    def create_fallback_strategy(self):
        """Create fallback strategy if no test data available"""
        
        return {
            'status': 'NO_TEST_DATA',
            'recommended_approach': 'Conservative third-party integration',
            'immediate_steps': [
                'Run scale tests to gather data',
                'Integrate Together AI for reliable Llama access',
                'Implement basic multi-provider system'
            ]
        }
    
    def save_strategy(self, filename='llama_integration_strategy.json'):
        """Save the strategy to a JSON file"""
        
        with open(filename, 'w') as f:
            json.dump(self.strategy, f, indent=2)
        
        print(f"📋 Strategy saved to {filename}")
    
    def print_executive_summary(self):
        """Print executive summary of the strategy"""
        
        print("🦙 LLAMA API INTEGRATION STRATEGY")
        print("=" * 60)
        
        if self.strategy.get('status') == 'NO_TEST_DATA':
            print("❌ No test data available - run scale tests first")
            return
        
        findings = self.strategy['primary_findings']
        
        print(f"📊 Current Status: {findings['llama_status']}")
        print("\n🔍 Key Issues Identified:")
        for issue in findings['issues_identified']:
            print(f"   • {issue}")
        
        print(f"\n🏆 Performance Ranking:")
        for rank in findings['performance_ranking']:
            print(f"   • {rank}")
        
        print(f"\n💰 Cost Ranking:")
        for rank in findings['cost_ranking']:
            print(f"   • {rank}")
        
        approaches = self.strategy['integration_approaches']
        print(f"\n🎯 Recommended Approach: {approaches['approach_2_third_party_providers']['name']}")
        print(f"   Priority: {approaches['approach_2_third_party_providers']['priority']}")
        print(f"   Effort: {approaches['approach_2_third_party_providers']['estimated_effort']}")
        
        phases = self.strategy['implementation_phases']
        print(f"\n📅 Implementation Timeline:")
        for phase_name, phase in phases.items():
            print(f"   • {phase_name}: {phase['timeline']} - {', '.join(phase['goals'])}")
        
        cost_opt = self.strategy['cost_optimization']
        print(f"\n💡 Cost Optimization Potential:")
        strategy_1 = cost_opt['optimization_strategies']['strategy_1_provider_mix']
        print(f"   • Mixed provider strategy: {strategy_1['savings']} savings")
        
        print(f"\n🚀 Next Steps:")
        phase_1 = phases['phase_1_immediate']
        for task in phase_1['tasks'][:3]:
            print(f"   1. {task}")

def main():
    """Main function to run the strategy analysis"""
    
    print("🧠 Analyzing Scale Test Results for Llama Integration Strategy...")
    
    strategy = LlamaIntegrationStrategy()
    strategy.print_executive_summary()
    strategy.save_strategy()
    
    print(f"\n✅ Strategy Analysis Complete!")
    print("📋 Detailed strategy saved to llama_integration_strategy.json")
    print("🎯 Ready to proceed with implementation!")

if __name__ == "__main__":
    main() 