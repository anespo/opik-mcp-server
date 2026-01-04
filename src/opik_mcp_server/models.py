"""
Data models for Opik MCP Server
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents supported"""
    SINGLE = "single"
    MULTI_AGENT = "multi_agent"
    AGENT2AGENT = "agent2agent"
    GRAPH = "graph"
    SWARM = "swarm"
    WORKFLOW = "workflow"


class EvaluationMetric(str, Enum):
    """Available evaluation metrics"""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    FACTUALITY = "factuality"
    HELPFULNESS = "helpfulness"
    TOXICITY = "toxicity"
    BIAS = "bias"
    CONVERSATION_QUALITY = "conversation_quality"
    AGENT_COORDINATION = "agent_coordination"
    WORKFLOW_EFFICIENCY = "workflow_efficiency"


class TestCase(BaseModel):
    """Individual test case for evaluation"""
    id: Optional[str] = None
    input: str = Field(..., description="Input prompt or message")
    expected_output: Optional[str] = Field(None, description="Expected response")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: Optional[str] = None


class AgentMessage(BaseModel):
    """Message in agent conversation"""
    from_agent: str = Field(..., description="Source agent identifier")
    to_agent: str = Field(..., description="Target agent identifier") 
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentConversation(BaseModel):
    """Multi-agent conversation flow"""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    agents: List[str] = Field(..., description="List of participating agents")
    messages: List[AgentMessage] = Field(..., description="Conversation messages")
    workflow_type: AgentType = Field(default=AgentType.MULTI_AGENT)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    """Request for single agent evaluation"""
    agent_id: str = Field(..., description="Agent identifier")
    test_cases: List[TestCase] = Field(..., description="Test cases to evaluate")
    evaluators: List[EvaluationMetric] = Field(..., description="Metrics to evaluate")
    project_name: Optional[str] = Field("default", description="Opik project name")
    experiment_name: Optional[str] = Field(None, description="Experiment name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MultiAgentEvaluationRequest(BaseModel):
    """Request for multi-agent system evaluation"""
    workflow_id: str = Field(..., description="Workflow identifier")
    workflow_type: AgentType = Field(..., description="Type of multi-agent workflow")
    conversation: AgentConversation = Field(..., description="Agent conversation to evaluate")
    evaluators: List[EvaluationMetric] = Field(..., description="Metrics to evaluate")
    project_name: Optional[str] = Field("default", description="Opik project name")
    experiment_name: Optional[str] = Field(None, description="Experiment name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EvaluationScore(BaseModel):
    """Individual evaluation score"""
    metric: EvaluationMetric = Field(..., description="Evaluation metric")
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    explanation: Optional[str] = Field(None, description="Explanation of the score")
    passed: bool = Field(..., description="Whether evaluation passed threshold")
    threshold: float = Field(0.7, description="Passing threshold")


class EvaluationResult(BaseModel):
    """Result of evaluation"""
    evaluation_id: str = Field(..., description="Unique evaluation identifier")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    workflow_id: Optional[str] = Field(None, description="Workflow identifier")
    test_case_id: Optional[str] = Field(None, description="Test case identifier")
    scores: List[EvaluationScore] = Field(..., description="Evaluation scores")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall score")
    passed: bool = Field(..., description="Whether overall evaluation passed")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    opik_trace_id: Optional[str] = Field(None, description="Opik trace identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BatchEvaluationResult(BaseModel):
    """Result of batch evaluation"""
    batch_id: str = Field(..., description="Batch identifier")
    results: List[EvaluationResult] = Field(..., description="Individual results")
    summary: Dict[str, Any] = Field(..., description="Batch summary statistics")
    total_tests: int = Field(..., description="Total number of tests")
    passed_tests: int = Field(..., description="Number of passed tests")
    failed_tests: int = Field(..., description="Number of failed tests")
    average_score: float = Field(..., description="Average score across all tests")
    execution_time_ms: float = Field(..., description="Total execution time")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OpikProject(BaseModel):
    """Opik project information"""
    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class OpikExperiment(BaseModel):
    """Opik experiment information"""
    id: str = Field(..., description="Experiment ID")
    name: str = Field(..., description="Experiment name")
    project_id: str = Field(..., description="Parent project ID")
    description: Optional[str] = Field(None, description="Experiment description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class OpikTrace(BaseModel):
    """Opik trace information"""
    id: str = Field(..., description="Trace ID")
    name: str = Field(..., description="Trace name")
    project_id: str = Field(..., description="Project ID")
    start_time: datetime = Field(..., description="Start timestamp")
    end_time: Optional[datetime] = Field(None, description="End timestamp")
    input: Optional[Dict[str, Any]] = Field(None, description="Trace input")
    output: Optional[Dict[str, Any]] = Field(None, description="Trace output")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)


class ServerStatus(BaseModel):
    """Server status information"""
    status: str = Field(..., description="Server status")
    version: str = Field(..., description="Server version")
    opik_connected: bool = Field(..., description="Opik connection status")
    agentcore_connected: bool = Field(..., description="AgentCore connection status")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    total_evaluations: int = Field(..., description="Total evaluations performed")
    active_sessions: int = Field(..., description="Active evaluation sessions")
    timestamp: datetime = Field(default_factory=datetime.utcnow)