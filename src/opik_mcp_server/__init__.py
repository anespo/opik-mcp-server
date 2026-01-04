"""
Opik MCP Server for Strands Agents Evaluation

A production-ready MCP server that integrates Opik evaluation framework 
with Strands Agents multi-agent systems, deployable on AWS Bedrock AgentCore.
"""

__version__ = "1.0.0"
__author__ = "Senior ML Engineer"
__email__ = "engineer@company.com"

from .server import app
from .models import *
from .evaluators import *

__all__ = [
    "app",
    "EvaluationRequest",
    "EvaluationResult", 
    "MultiAgentEvaluationRequest",
    "AgentConversation",
    "OpikEvaluator",
    "StrandsAgentEvaluator",
    "MultiAgentEvaluator"
]