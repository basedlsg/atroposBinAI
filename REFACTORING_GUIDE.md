# Code Refactoring Integration Guide

This guide explains the refactorings made to improve code quality and how to integrate them into your project.

## Overview of Changes

### 1. New Utility Modules Created

#### `spatial_rl_mvp/config.py`
- Centralizes all configuration constants
- Eliminates magic numbers throughout the codebase
- Makes tuning and adjustments easier

**Usage:**
```python
from spatial_rl_mvp.config import SCORING, LLM, TASK, PHYSICS, VISUALIZATION

# Use constants instead of hardcoded values
if distance <= target_distance * SCORING.GOOD_DISTANCE_THRESHOLD:
    score = SCORING.SCORE_GOOD
```

#### `spatial_rl_mvp/exceptions.py`
- Custom exception hierarchy for better error handling
- Makes it easier to catch specific error types

**Usage:**
```python
from spatial_rl_mvp.exceptions import TaskNotInitializedError, SimulationError

try:
    await env.apply_action(action)
except TaskNotInitializedError:
    # Handle case where task wasn't initialized
    pass
except SimulationError as e:
    # Handle physics simulation errors
    logger.error(f"Simulation failed: {e}")
```

#### `spatial_rl_mvp/logger.py`
- Consistent structured logging across all modules
- Replaces inconsistent print() statements

**Usage:**
```python
from spatial_rl_mvp.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Task initialized successfully")
logger.warning("LLM call timed out")
logger.error("Failed to move object", exc_info=True)
```

#### `spatial_rl_mvp/scoring.py`
- Encapsulates all scoring logic
- Easier to test and modify scoring algorithms
- Better documentation of scoring rules

**Usage:**
```python
from spatial_rl_mvp.scoring import SpatialScorer

scorer = SpatialScorer()
score, metadata = scorer.calculate_score(
    distance=1.2,
    target_distance=1.0,
    target_pos=[1.0, 0.0, 0.5],
    reference_pos=[0.0, 0.0, 0.5]
)
```

---

### 2. Refactored Main Files

#### `spatial_rl_mvp/spatial_env_refactored.py`

**Key Improvements:**
- ✅ Removed global state (`global_physics_simulator_instance`, `shared_demo_runner_instance`)
- ✅ Added `enable_visualization` flag (no more monkey-patching needed!)
- ✅ Broke up massive `collect_trajectories` method into smaller, focused functions
- ✅ Replaced all `print()` with structured logging
- ✅ Uses new config, exceptions, and scoring modules
- ✅ Proper dependency injection for WebSocket handler

**Migration Path:**
```python
# OLD WAY (global state)
global_physics_simulator_instance = simulator
env = SpatialEnvironmentMVP()

# NEW WAY (clean initialization)
env = SpatialEnvironmentMVP(enable_visualization=False)  # For API mode
env = SpatialEnvironmentMVP(enable_visualization=True)   # For server mode
```

**To Integrate:**
1. Replace import: `from spatial_rl_mvp.spatial_env import ...`
   → `from spatial_rl_mvp.spatial_env_refactored import ...`
2. Remove any code that manipulates global variables
3. Pass `enable_visualization=False` when creating env for API use

#### `padres_container/app/main_refactored.py`

**Key Improvements:**
- ✅ No monkey-patching!
- ✅ Clean initialization with `enable_visualization=False`
- ✅ Better error handling and logging

**Migration Path:**
```python
# OLD WAY (monkey-patching)
sys.modules['spatial_rl_mvp.spatial_env'].notify_visualization_clients = dummy_func
env = SpatialEnvironmentMVP()

# NEW WAY (clean configuration)
env = SpatialEnvironmentMVP(enable_visualization=False)
```

**To Integrate:**
1. Update Dockerfile to use `main_refactored.py`
2. Update imports to use refactored modules
3. Remove all monkey-patching code

#### `enhanced_padres_perplexity_refactored.py`

**Key Improvements:**
- ✅ Async/await throughout
- ✅ Connection pooling with aiohttp
- ✅ Proper resource management with context managers
- ✅ Better error handling

**Migration Path:**
```python
# OLD WAY (synchronous, no pooling)
researcher = SimplePadresResearch()
result = researcher.run_research_experiment()

# NEW WAY (async with pooling)
async with SimplePadresResearch() as researcher:
    result = await researcher.run_research_experiment()
```

**To Integrate:**
1. Update `production_research_pipeline.py` to import refactored version
2. Make sure all calling code is async
3. Use context manager for proper cleanup

---

## Integration Steps

### Step 1: Add aiohttp Dependency
```bash
pip install aiohttp
```

Or add to `requirements.txt`:
```
aiohttp>=3.9.0
```

### Step 2: Test Refactored Modules Individually

```bash
# Test config module
python -c "from spatial_rl_mvp.config import SCORING; print(SCORING)"

# Test logger
python -c "from spatial_rl_mvp.logger import setup_logger; logger = setup_logger('test'); logger.info('Works!')"

# Test scoring
python -c "from spatial_rl_mvp.scoring import SpatialScorer; s = SpatialScorer(); print(s)"

# Test exceptions
python -c "from spatial_rl_mvp.exceptions import TaskNotInitializedError; print(TaskNotInitializedError)"
```

### Step 3: Gradually Migrate

**Option A: Side-by-Side (Recommended)**
- Keep original files as backup
- Use refactored files with `_refactored` suffix
- Test thoroughly before replacing originals

**Option B: Direct Replacement**
```bash
cd spatial_rl_mvp
mv spatial_env.py spatial_env_old.py
mv spatial_env_refactored.py spatial_env.py

cd ../padres_container/app
mv main.py main_old.py
mv main_refactored.py main.py

cd ../..
mv enhanced_padres_perplexity.py enhanced_padres_perplexity_old.py
mv enhanced_padres_perplexity_refactored.py enhanced_padres_perplexity.py
```

### Step 4: Update Import Statements

If using Option A (side-by-side), update imports:

```python
# In files that use spatial environment
from spatial_rl_mvp.spatial_env_refactored import (
    SpatialEnvironmentMVP,
    SpatialTask,
    ObjectState,
    MVPDemoRunner
)

# In production pipeline
from enhanced_padres_perplexity_refactored import SimplePadresResearch
```

### Step 5: Update production_research_pipeline.py

Make it async and use connection pooling:

```python
from enhanced_padres_perplexity_refactored import SimplePadresResearch

class Production24x7Pipeline:
    async def __aenter__(self):
        self.researcher = SimplePadresResearch()
        # ... other setup
        return self

    async def __aexit__(self, *args):
        await self.researcher.cleanup()

    async def run_experiment_batch(self, batch_size: int):
        # Use await for async calls
        result = await self.researcher.run_research_experiment()
        # ...
```

### Step 6: Update Docker Configuration

Update `padres_container/Dockerfile` if needed:

```dockerfile
# Make sure CMD points to refactored file
CMD ["uvicorn", "app.main_refactored:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## Testing the Changes

### Unit Tests

Create `spatial_rl_mvp/tests/test_scoring.py`:

```python
import pytest
from spatial_rl_mvp.scoring import SpatialScorer
from spatial_rl_mvp.config import SCORING

def test_perfect_score():
    scorer = SpatialScorer()
    score, metadata = scorer.calculate_score(
        distance=1.0,
        target_distance=1.0,
        target_pos=[1.0, 0, 0],
        reference_pos=[0, 0, 0]
    )
    expected = SCORING.SCORE_EXCELLENT + SCORING.SCORE_SIDE_CONDITION_BONUS
    assert score == expected
    assert metadata['side_condition_met'] is True
```

### Integration Tests

```bash
# Test spatial environment
python spatial_rl_mvp/spatial_env_refactored.py process --num_turns 2

# Test Padres API
# (Start the refactored server first)
curl http://localhost:8080/status
curl -X POST http://localhost:8080/setup_environment
curl -X POST http://localhost:8080/execute_action
```

### Performance Testing

Compare old vs new with connection pooling:

```python
import asyncio
import time

async def test_connection_pooling():
    from enhanced_padres_perplexity_refactored import SimplePadresResearch

    async with SimplePadresResearch() as researcher:
        start = time.time()

        # Run multiple requests that will reuse connections
        tasks = [
            researcher.search_perplexity("AI research")
            for _ in range(10)
        ]
        await asyncio.gather(*tasks)

        duration = time.time() - start
        print(f"10 requests completed in {duration:.2f}s")

asyncio.run(test_connection_pooling())
```

---

## Configuration Tuning

### Adjusting Scoring

Edit `spatial_rl_mvp/config.py`:

```python
@dataclass
class ScoringConfig:
    # Make distance thresholds more lenient
    EXCELLENT_DISTANCE_THRESHOLD: float = 1.2  # was 1.0
    GOOD_DISTANCE_THRESHOLD: float = 1.5       # was 1.25

    # Increase side condition bonus
    SCORE_SIDE_CONDITION_BONUS: float = 0.3    # was 0.2
```

### Adjusting LLM Timeouts

```python
@dataclass
class LLMConfig:
    TIMEOUT_SECONDS: int = 45  # Increase from 30
    MAX_RETRIES: int = 5       # Increase from 3
```

### Adjusting Connection Pool

Edit `enhanced_padres_perplexity_refactored.py`:

```python
connector = aiohttp.TCPConnector(
    limit=200,           # Increase max connections
    limit_per_host=50,  # Increase per-host limit
    ttl_dns_cache=600   # Increase DNS cache TTL
)
```

---

## Rollback Plan

If issues arise:

1. **Keep backups of original files**
2. **Use git to revert**:
   ```bash
   git checkout -- spatial_rl_mvp/spatial_env.py
   ```
3. **Or restore from backups**:
   ```bash
   mv spatial_env_old.py spatial_env.py
   ```

---

## Benefits Summary

### Code Quality
- ✅ No global state
- ✅ Better separation of concerns
- ✅ Easier to test
- ✅ More maintainable

### Performance
- ✅ Connection pooling reduces overhead
- ✅ Async/await improves throughput
- ✅ Better resource management

### Reliability
- ✅ Proper error handling
- ✅ Structured logging for debugging
- ✅ Resource cleanup with context managers

### Developer Experience
- ✅ Configuration in one place
- ✅ Clear exception types
- ✅ Self-documenting code
- ✅ No monkey-patching surprises

---

## Next Steps

1. Review the refactored files
2. Run existing tests to ensure compatibility
3. Gradually integrate changes
4. Monitor performance in production
5. Iterate based on feedback

## Questions?

If you encounter issues:
1. Check logs for detailed error messages
2. Verify all environment variables are set
3. Ensure aiohttp is installed
4. Review this guide's troubleshooting section

---

**Last Updated:** 2025-01-15
**Refactored By:** Code Quality Improvement Initiative
