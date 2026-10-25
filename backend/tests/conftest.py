"""Pytest fixtures and environment configuration for testing."""

import os
import pytest

# Ensure dummy keys are present during unit testing if not set
os.environ.setdefault("NEBIUS_API_KEY", "test-nebius-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("MODEL_FAST", "nvidia/Nemotron-3-Nano-30B-A3B")
os.environ.setdefault("MODEL_REASONING", "nvidia/Nemotron-3-Ultra-550b-a55b")
