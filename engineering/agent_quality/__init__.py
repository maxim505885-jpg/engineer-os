"""ENGINEER OS agent quality gates adapted from Clod-/ECC ideas.

This package validates agent contracts and regression scenarios. It does not
decide engineering truth and does not replace Result Validator or FINAL AUDIT.
"""

from .harness import AgentHarness, AgentQualityCase, AgentQualityResult

__all__ = ["AgentHarness", "AgentQualityCase", "AgentQualityResult"]
