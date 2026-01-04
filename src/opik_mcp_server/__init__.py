"""
Opik MCP Server for AI Agent Evaluation

A production-ready MCP server that integrates Opik evaluation framework 
with AI agents and multi-agent systems, deployable on AWS Bedrock AgentCore.
"""

__version__ = "1.0.0"
__author__ = "Tony Esposito"
__email__ = "tony@mydataclub.com"

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
    "AgentEvaluator",
    "MultiAgentEvaluator"
]
