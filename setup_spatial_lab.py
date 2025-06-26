#!/usr/bin/env python3
"""
Setup script for Spatial AI Research Lab

Installs dependencies and configures the environment for spatial reasoning experiments.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(command, description=""):
    """Run a shell command and handle errors"""
    logger.info(f"Running: {command}")
    if description:
        logger.info(f"Description: {description}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    logger.info(f"Python version: {sys.version}")
    return True


def install_dependencies():
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    
    # Core dependencies
    dependencies = [
        "numpy>=1.21.0",
        "scipy>=1.7.0", 
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0",
        "scikit-learn>=1.0.0",
        "pydantic>=1.8.0",
        "aiofiles>=0.7.0",
        "wandb>=0.12.0",
        "tqdm>=4.62.0",
        "pytest>=6.2.0",
        "pytest-asyncio>=0.18.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            logger.warning(f"Failed to install {dep}")
    
    # Install Atropos dependencies
    logger.info("Installing Atropos dependencies...")
    atropos_path = Path("atroposBinAI")
    if atropos_path.exists():
        if not run_command(f"pip install -e {atropos_path}", "Installing Atropos in development mode"):
            logger.warning("Failed to install Atropos")
    else:
        logger.warning("Atropos directory not found")
    
    logger.info("Dependencies installation completed")


def setup_directories():
    """Create necessary directories"""
    logger.info("Setting up directories...")
    
    directories = [
        "results",
        "configs", 
        "logs",
        "checkpoints",
        "data/warehouse_layouts",
        "data/evaluation_results",
        "src/spatial_lab/tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def create_config_files():
    """Create initial configuration files"""
    logger.info("Creating configuration files...")
    
    # Create basic experiment config
    basic_config = {
        "experiment_name": "basic_warehouse_test",
        "description": "Test configuration for spatial reasoning lab",
        "environment": {
            "warehouse_width": 30.0,
            "warehouse_height": 20.0,
            "num_robots": 3,
            "num_shelves": 10
        },
        "tasks": {
            "complexity": "easy",
            "max_duration": 200,
            "items_per_task": 5,
            "num_evaluation_tasks": 10
        },
        "training": {
            "num_episodes": 20,
            "batch_size": 16,
            "learning_rate": 0.001
        },
        "model": {
            "name": "gpt-4o-mini",
            "max_tokens": 256,
            "temperature": 0.7
        },
        "infrastructure": {
            "use_wandb": False,
            "save_trajectories": True,
            "output_dir": "results"
        }
    }
    
    import json
    config_file = Path("configs/test_config.json")
    with open(config_file, 'w') as f:
        json.dump(basic_config, f, indent=2)
    
    logger.info(f"Created test configuration: {config_file}")


def setup_environment_variables():
    """Setup environment variables"""
    logger.info("Setting up environment variables...")
    
    env_file = Path(".env")
    
    env_content = """# Spatial AI Research Lab Environment Variables

# OpenAI API (required for LLM inference)
# OPENAI_API_KEY=your_openai_api_key_here

# Weights & Biases (optional, for experiment tracking)
# WANDB_API_KEY=your_wandb_api_key_here
# WANDB_PROJECT=spatial-ai-research-lab

# Experiment settings
SPATIAL_LAB_OUTPUT_DIR=results
SPATIAL_LAB_LOG_LEVEL=INFO

# Development settings
PYTHONPATH=${PYTHONPATH}:./src:./atroposBinAI
"""
    
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        logger.info(f"Created environment file: {env_file}")
    else:
        logger.info("Environment file already exists")


def run_tests():
    """Run basic tests to verify installation"""
    logger.info("Running basic tests...")
    
    # Test imports
    test_imports = [
        "import numpy as np",
        "import scipy",
        "import pandas as pd",
        "from pathlib import Path",
        "import asyncio",
        "from pydantic import BaseModel"
    ]
    
    for test_import in test_imports:
        try:
            exec(test_import)
            logger.info(f"✓ {test_import}")
        except ImportError as e:
            logger.error(f"✗ {test_import} - {e}")
    
    # Test spatial lab imports
    try:
        sys.path.insert(0, str(Path("src").absolute()))
        from spatial_lab.config import get_config
        config = get_config("basic_warehouse")
        logger.info("✓ Spatial lab configuration system working")
    except Exception as e:
        logger.error(f"✗ Spatial lab import failed: {e}")
    
    logger.info("Basic tests completed")


def main():
    """Main setup function"""
    logger.info("Starting Spatial AI Research Lab setup...")
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    setup_directories()
    install_dependencies()
    create_config_files()
    setup_environment_variables()
    run_tests()
    
    logger.info("Setup completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Set your OpenAI API key in the .env file")
    logger.info("2. (Optional) Set your Weights & Biases API key for experiment tracking")
    logger.info("3. Run a test experiment: python -m src.spatial_lab.experiment_runner --config test_config")
    logger.info("")
    logger.info("For more information, see the documentation in docs/")


if __name__ == "__main__":
    main() 