#!/usr/bin/env python3
"""
Dependency Security Check Script

This script checks for vulnerable dependencies using Safety.
It should be run in CI/CD pipelines to prevent vulnerable dependencies from being deployed.

Usage:
    python check_dependencies.py

Exit codes:
    0: All dependencies are secure
    1: Vulnerable dependencies found
    2: Error running security check
"""

import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check dependencies for known vulnerabilities using Safety."""

    try:
        # Check if safety is installed
        try:
            import safety.cli
        except ImportError:
            logger.info("Installing Safety for dependency scanning...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "safety"], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install Safety: {e}")
                return 2

        logger.info("Running dependency security scan...")

        # Run safety check
        result = subprocess.run(["safety", "check", "--full-report", "--json"], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ No vulnerable dependencies found")
            return 0
        else:
            logger.error("❌ Vulnerable dependencies detected!")
            logger.error("Safety output:")
            logger.error(result.stdout)
            if result.stderr:
                logger.error("Errors:")
                logger.error(result.stderr)
            return 1

    except Exception as e:
        logger.error(f"Error running dependency security check: {e}")
        return 2


if __name__ == "__main__":
    # Change to the backend directory
    backend_dir = Path(__file__).parent.parent / "backend"
    if backend_dir.exists():
        import os

        os.chdir(backend_dir)

    exit_code = check_dependencies()
    sys.exit(exit_code)
