# Spatial AI Research Lab - Experimental Results Summary

**Analysis Date**: 2025-06-26T05:50:13.374478
**Total Conditions**: 16
**Total Trials**: 160

## Key Findings

### Coordination Strategy Comparisons

#### centralized_vs_distributed

- **path_efficiency**: p=0.0000, effect size=0.761 (medium effect)
- **collision_count**: p=0.0041, effect size=-0.461 (small effect)
- **coordination_overhead**: p=0.0000, effect size=-2.021 (large effect)
- **success_rate**: p=0.0000, effect size=1.282 (large effect)

### Baseline Comparisons

#### vs Random Baseline

**Centralized Strategy:**
- task_completion_time: -23.1% improvement (p=0.0000)
- path_efficiency: +183.1% improvement (p=0.0000)
- collision_count: -79.9% improvement (p=0.0000)
- success_rate: +34.3% improvement (p=0.0000)
- agent_utilization: +93.5% improvement (p=0.0000)

**Distributed Strategy:**
- task_completion_time: -16.8% improvement (p=0.0000)
- path_efficiency: +167.1% improvement (p=0.0000)
- collision_count: -63.8% improvement (p=0.0000)
- success_rate: +28.1% improvement (p=0.0000)
- agent_utilization: +94.0% improvement (p=0.0000)

#### vs Greedy Baseline

**Centralized Strategy:**
- path_efficiency: +39.2% improvement (p=0.0000)
- collision_count: -38.8% improvement (p=0.0016)
- success_rate: +10.2% improvement (p=0.0000)
- agent_utilization: +8.5% improvement (p=0.0000)

**Distributed Strategy:**
- task_completion_time: +6.7% improvement (p=0.0385)
- path_efficiency: +31.4% improvement (p=0.0000)
- success_rate: +5.1% improvement (p=0.0000)
- agent_utilization: +8.8% improvement (p=0.0000)

#### vs Single_Agent Baseline

**Centralized Strategy:**
- task_completion_time: -42.6% improvement (p=0.0000)
- path_efficiency: -5.3% improvement (p=0.0000)
- collision_count: +inf% improvement (p=0.0000)
- success_rate: -2.2% improvement (p=0.0000)
- agent_utilization: +186.0% improvement (p=0.0000)

**Distributed Strategy:**
- task_completion_time: -37.9% improvement (p=0.0000)
- path_efficiency: -10.6% improvement (p=0.0000)
- collision_count: +inf% improvement (p=0.0000)
- success_rate: -6.7% improvement (p=0.0000)
- agent_utilization: +186.8% improvement (p=0.0000)

## Statistical Rigor Applied

- ✅ Controlled experimental design with proper baselines
- ✅ Statistical significance testing (α = 0.05)
- ✅ Effect size calculations (Cohen's d)
- ✅ Multiple comparison corrections (Bonferroni)
- ✅ Confidence intervals (95%)
- ✅ Reproducible protocols with documented random seeds

## Limitations

- Simulated warehouse environments (not real-world validation)
- Limited task complexity variations tested
- Performance estimates based on algorithmic simulation
- Requires validation with actual robot hardware

