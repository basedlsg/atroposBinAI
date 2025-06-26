#!/usr/bin/env python3

"""
Real LLM API Integration Test

Tests the integration of Llama and Gemini APIs with our Spatial AI Lab.
Uses the actual API keys provided to validate connectivity and spatial reasoning.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from spatial_lab.llm import (
    create_llm_coordinator,
    test_llama_api,
    test_gemini_api,
    TaskRequirements,
    LLMProvider
)
from spatial_lab.environments.warehouse_environment import (
    WarehouseSpatialEnvironment,
    WarehouseSpatialEnvironmentConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys (provided by user)
LLAMA_API_KEY = "LLM|1469017110898899|mJOyVVo1xc4vbUj6y1Wj-svovnE"
GEMINI_API_KEY = "AIzaSyAqko3NqGS-GtXhzm8LeiZ3xUEyo_XIqLo"


async def test_api_connectivity():
    """Test basic connectivity to both APIs"""
    
    logger.info("🔍 Testing API Connectivity...")
    
    # Test Llama API
    logger.info("Testing Llama API...")
    llama_success = await test_llama_api(LLAMA_API_KEY)
    
    # Test Gemini API  
    logger.info("Testing Gemini API...")
    gemini_success = await test_gemini_api(GEMINI_API_KEY)
    
    logger.info(f"✅ Llama API: {'CONNECTED' if llama_success else 'FAILED'}")
    logger.info(f"✅ Gemini API: {'CONNECTED' if gemini_success else 'FAILED'}")
    
    return llama_success, gemini_success


async def test_llm_coordinator():
    """Test the LLM coordinator with both providers"""
    
    logger.info("🤖 Testing LLM Coordinator...")
    
    # Create coordinator with both APIs
    coordinator = create_llm_coordinator(
        llama_api_key=LLAMA_API_KEY,
        gemini_api_key=GEMINI_API_KEY,
        preferred_provider="llama"
    )
    
    # Test provider connectivity
    test_results = await coordinator.test_all_providers()
    logger.info(f"Provider test results: {test_results}")
    
    # Test robot coordination decision
    logger.info("Testing robot coordination decision...")
    
    # Mock robot observation data
    robot_observation = {
        "robot_state": {
            "position": (10.0, 5.0, 0.0),
            "orientation": 0.0,
            "carrying_item": None,
            "battery_level": 0.85,
            "current_task": "collect_items",
            "status": "idle"
        },
        "local_observation": {
            "visible_items": ["item_001", "item_002"],
            "visible_obstacles": [],
            "path_clear": True
        },
        "warehouse_context": {
            "nearby_shelves": [
                {"shelf_id": "shelf_A1", "position": (8.0, 3.0), "items": ["item_001"]},
                {"shelf_id": "shelf_A2", "position": (12.0, 7.0), "items": ["item_002"]}
            ],
            "nearby_robots": [
                {"robot_id": "robot_002", "position": (15.0, 8.0), "status": "moving"}
            ],
            "available_items": ["item_001", "item_002"],
            "current_congestion": 0.2
        },
        "timestamp": time.time()
    }
    
    try:
        response, provider_used = await coordinator.robot_coordination_decision(
            robot_id="robot_001",
            observation=robot_observation,
            task_description="Collect items from shelves A1 and A2, deliver to zone C",
            available_actions=["move_to", "pick_item", "drop_item", "wait", "communicate"],
            nearby_robots=[{"robot_id": "robot_002", "position": (15.0, 8.0), "status": "moving"}],
            warehouse_layout={
                "shelves": [
                    {"shelf_id": "shelf_A1", "position": (8.0, 3.0)},
                    {"shelf_id": "shelf_A2", "position": (12.0, 7.0)}
                ],
                "dimensions": (50.0, 30.0)
            }
        )
        
        logger.info(f"✅ Robot decision successful using provider: {provider_used}")
        logger.info(f"Response preview: {str(response)[:200]}...")
        
        # Try to extract the decision
        if "completion_message" in response:
            content = response["completion_message"]["content"]
            if isinstance(content, dict) and "text" in content:
                decision_text = content["text"]
                logger.info(f"Decision text: {decision_text}")
                
                # Try to parse as JSON
                try:
                    decision_data = json.loads(decision_text)
                    logger.info(f"Parsed decision: {decision_data}")
                except json.JSONDecodeError:
                    logger.warning("Decision is not valid JSON")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Robot coordination decision failed: {e}")
        return False


async def test_warehouse_environment_integration():
    """Test the full warehouse environment with real LLM integration"""
    
    logger.info("🏭 Testing Warehouse Environment with Real LLMs...")
    
    # Create warehouse environment config with real API keys
    config = WarehouseSpatialEnvironmentConfig(
        warehouse_width=40.0,
        warehouse_height=25.0,
        num_robots=3,
        num_shelves=10,
        llama_api_key=LLAMA_API_KEY,
        gemini_api_key=GEMINI_API_KEY,
        preferred_llm_provider="llama",
        max_task_duration=50  # Shorter for testing
    )
    
    # Create dummy server config (required by Atropos)
    from atroposlib.envs.server_handling.server_baseline import APIServerConfig
    dummy_server_config = APIServerConfig(
        model_name="test_model",
        base_url="http://localhost:8000",
        api_key="test_key",
        num_requests_for_eval=1,
        max_tokens=100,
        temperature=0.7
    )
    
    try:
        # Create environment
        env = WarehouseSpatialEnvironment(config=config, server_configs=[dummy_server_config])
        await env.setup()
        
        logger.info("✅ Warehouse environment initialized successfully")
        
        # Generate a task
        task_item = await env.get_next_item()
        logger.info(f"✅ Generated task: {task_item['item_id']}")
        
        # Test robot observations
        observations = await env.get_robot_observations()
        logger.info(f"✅ Got observations for {len(observations)} robots")
        
        # Test robot decisions with real LLMs
        task_data = task_item["data"]["task"]
        from spatial_lab.environments.warehouse_tasks import WarehouseTask
        task = WarehouseTask.from_dict(task_data)
        
        logger.info("🧠 Getting robot decisions from real LLMs...")
        decisions = await env.get_robot_decisions(observations, task)
        
        logger.info(f"✅ Got decisions for {len(decisions)} robots")
        
        # Display decisions
        for robot_id, decision in decisions.items():
            provider = decision.get("provider_used", "unknown")
            action = decision.get("action", "unknown")
            reasoning = decision.get("reasoning", "No reasoning")
            confidence = decision.get("confidence", 0.0)
            
            logger.info(f"Robot {robot_id} [{provider}]: {action} (confidence: {confidence:.2f})")
            logger.info(f"  Reasoning: {reasoning}")
        
        # Get performance report from LLM coordinator
        if env.llm_coordinator:
            performance_report = env.llm_coordinator.get_performance_report()
            logger.info(f"LLM Performance Report: {json.dumps(performance_report, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Warehouse environment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_spatial_reasoning_capabilities():
    """Test advanced spatial reasoning capabilities"""
    
    logger.info("🧭 Testing Advanced Spatial Reasoning...")
    
    coordinator = create_llm_coordinator(
        llama_api_key=LLAMA_API_KEY,
        gemini_api_key=GEMINI_API_KEY,
        preferred_provider="llama"
    )
    
    # Test warehouse layout analysis
    layout_data = {
        "dimensions": (50.0, 30.0),
        "shelves": [
            {"id": "A1", "position": (5, 5), "size": (2, 8), "capacity": 100},
            {"id": "A2", "position": (5, 15), "size": (2, 8), "capacity": 100},
            {"id": "B1", "position": (15, 5), "size": (2, 8), "capacity": 100},
            {"id": "B2", "position": (15, 15), "size": (2, 8), "capacity": 100},
            {"id": "C1", "position": (25, 5), "size": (2, 8), "capacity": 100}
        ],
        "aisles": [
            {"id": "main_aisle", "start": (0, 10), "end": (50, 10), "width": 3},
            {"id": "cross_aisle_1", "start": (10, 0), "end": (10, 30), "width": 2},
            {"id": "cross_aisle_2", "start": (20, 0), "end": (20, 30), "width": 2}
        ],
        "zones": [
            {"id": "receiving", "area": (0, 0, 10, 5)},
            {"id": "shipping", "area": (40, 0, 50, 5)},
            {"id": "storage", "area": (10, 5, 40, 25)}
        ]
    }
    
    try:
        # Test with Llama first
        async with await coordinator.get_client() as client:
            if LLMProvider.LLAMA in coordinator.providers:
                response = await client.analyze_warehouse_layout(
                    layout_data=layout_data,
                    optimization_goals=["efficiency", "safety", "throughput"]
                )
                
                logger.info("✅ Warehouse layout analysis completed")
                logger.info(f"Response preview: {str(response)[:300]}...")
                
                return True
            else:
                logger.warning("Llama provider not available for layout analysis")
                return False
        
    except Exception as e:
        logger.error(f"❌ Spatial reasoning test failed: {e}")
        return False


async def main():
    """Run all LLM API integration tests"""
    
    logger.info("🚀 Starting Real LLM API Integration Tests")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: API Connectivity
    logger.info("\n" + "=" * 60)
    llama_connected, gemini_connected = await test_api_connectivity()
    test_results["api_connectivity"] = llama_connected or gemini_connected
    
    if not (llama_connected or gemini_connected):
        logger.error("❌ No APIs are accessible. Stopping tests.")
        return
    
    # Test 2: LLM Coordinator
    logger.info("\n" + "=" * 60)
    coordinator_success = await test_llm_coordinator()
    test_results["llm_coordinator"] = coordinator_success
    
    # Test 3: Warehouse Environment Integration
    logger.info("\n" + "=" * 60)
    warehouse_success = await test_warehouse_environment_integration()
    test_results["warehouse_integration"] = warehouse_success
    
    # Test 4: Advanced Spatial Reasoning
    logger.info("\n" + "=" * 60)
    spatial_success = await test_spatial_reasoning_capabilities()
    test_results["spatial_reasoning"] = spatial_success
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 TEST SUMMARY")
    logger.info("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:.<30} {status}")
    
    logger.info("-" * 60)
    logger.info(f"TOTAL: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! Real LLM APIs are fully integrated!")
    elif passed_tests > 0:
        logger.info("⚠️  PARTIAL SUCCESS: Some tests passed, system is partially functional")
    else:
        logger.error("💥 ALL TESTS FAILED: LLM integration needs attention")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main()) 