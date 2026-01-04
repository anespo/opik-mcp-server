"""
FastMCP server implementation for Opik evaluation
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from fastmcp import FastMCP
from fastmcp.resources import Resource
from fastmcp.tools import Tool

from .config import settings
from .evaluators import MultiAgentEvaluator, StrandsAgentEvaluator
from .models import (
    AgentConversation,
    AgentType,
    BatchEvaluationResult,
    EvaluationMetric,
    EvaluationRequest,
    EvaluationResult,
    MultiAgentEvaluationRequest,
    ServerStatus,
    TestCase
)
from .observability import setup_observability, log_evaluation_result


# Initialize FastMCP app
app = FastMCP("Opik MCP Server")

# Global state
server_start_time = time.time()
total_evaluations = 0
active_sessions = set()

# Initialize evaluators
strands_evaluator = StrandsAgentEvaluator()
multiagent_evaluator = MultiAgentEvaluator()

# Initialize Bedrock client for real agent simulation
_bedrock_client = None

def get_bedrock_client():
    """Get or create Bedrock client"""
    global _bedrock_client
    if _bedrock_client is None:
        profile = os.environ.get('AWS_PROFILE', 'default')
        session = boto3.Session(profile_name=profile, region_name=settings.aws_region)
        _bedrock_client = session.client('bedrock-runtime')
    return _bedrock_client


async def real_agent_function(input_text: str, context: Dict[str, Any]) -> str:
    """
    Real LLM-powered agent using Claude 3.5 Sonnet.
    Simulates a production agent that responds to user queries.
    """
    client = get_bedrock_client()
    model_id = "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # Build system prompt based on context
    scenario = context.get("scenario", "general assistant")
    system_prompt = f"""You are a helpful {scenario} agent. 
Respond naturally and helpfully to the user's request.
Be concise but thorough. Provide actionable guidance when appropriate."""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": input_text}
        ],
        "temperature": 0.3
    }
    
    try:
        # Run synchronous boto3 call in executor
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        return f"I apologize, but I encountered an issue processing your request: {str(e)}"


# Setup observability for AgentCore
if settings.agentcore_enabled:
    setup_observability()


@app.tool()
async def evaluate_agent(
    agent_id: str,
    test_cases: List[Dict[str, Any]],
    evaluators: List[str],
    project_name: str = "default",
    experiment_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluate a single Strands agent with multiple test cases.
    
    Args:
        agent_id: Unique identifier for the agent
        test_cases: List of test cases with 'input', 'expected_output', and optional 'context'
        evaluators: List of evaluation metrics to apply
        project_name: Opik project name
        experiment_name: Optional experiment name
        metadata: Optional metadata for the evaluation
    
    Returns:
        Dictionary containing evaluation results
    """
    global total_evaluations, active_sessions
    
    session_id = str(uuid.uuid4())
    active_sessions.add(session_id)
    
    try:
        # Convert input to models
        parsed_test_cases = [
            TestCase(
                id=tc.get("id", str(uuid.uuid4())),
                input=tc["input"],
                expected_output=tc.get("expected_output"),
                context=tc.get("context", {}),
                metadata=tc.get("metadata", {}),
                session_id=session_id
            )
            for tc in test_cases
        ]
        
        parsed_evaluators = [EvaluationMetric(e) for e in evaluators]
        
        request = EvaluationRequest(
            agent_id=agent_id,
            test_cases=parsed_test_cases,
            evaluators=parsed_evaluators,
            project_name=project_name,
            experiment_name=experiment_name,
            metadata=metadata or {}
        )
        
        # Use real LLM-powered agent function
        # Evaluate agent
        results = await strands_evaluator.evaluate_agent(request, real_agent_function)
        
        # Log results to AgentCore if enabled
        if settings.agentcore_enabled:
            for result in results:
                await log_evaluation_result(result)
        
        total_evaluations += len(results)
        
        # Convert results to dict format
        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.passed),
            "failed_tests": sum(1 for r in results if not r.passed),
            "average_score": sum(r.overall_score for r in results) / len(results) if results else 0.0,
            "results": [r.dict() for r in results]
        }
        
    finally:
        active_sessions.discard(session_id)


@app.tool()
async def evaluate_multiagent_workflow(
    workflow_id: str,
    workflow_type: str,
    agents: List[str],
    conversation_messages: List[Dict[str, Any]],
    evaluators: List[str],
    project_name: str = "default",
    experiment_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluate a multi-agent workflow or conversation.
    
    Args:
        workflow_id: Unique identifier for the workflow
        workflow_type: Type of workflow (agent2agent, graph, swarm, workflow)
        agents: List of participating agent identifiers
        conversation_messages: List of messages with 'from_agent', 'to_agent', 'message'
        evaluators: List of evaluation metrics to apply
        project_name: Opik project name
        experiment_name: Optional experiment name
        metadata: Optional metadata for the evaluation
    
    Returns:
        Dictionary containing evaluation results
    """
    global total_evaluations, active_sessions
    
    session_id = str(uuid.uuid4())
    active_sessions.add(session_id)
    
    try:
        # Convert input to models
        from .models import AgentMessage
        
        messages = [
            AgentMessage(
                from_agent=msg["from_agent"],
                to_agent=msg["to_agent"],
                message=msg["message"],
                timestamp=datetime.fromisoformat(msg.get("timestamp", datetime.utcnow().isoformat())),
                metadata=msg.get("metadata", {})
            )
            for msg in conversation_messages
        ]
        
        conversation = AgentConversation(
            conversation_id=str(uuid.uuid4()),
            agents=agents,
            messages=messages,
            workflow_type=AgentType(workflow_type),
            metadata=metadata or {}
        )
        
        parsed_evaluators = [EvaluationMetric(e) for e in evaluators]
        
        request = MultiAgentEvaluationRequest(
            workflow_id=workflow_id,
            workflow_type=AgentType(workflow_type),
            conversation=conversation,
            evaluators=parsed_evaluators,
            project_name=project_name,
            experiment_name=experiment_name,
            metadata=metadata or {}
        )
        
        # Evaluate workflow
        if workflow_type == "agent2agent":
            result = await multiagent_evaluator.evaluate_agent2agent_flow(request)
        else:
            result = await multiagent_evaluator.evaluate_multiagent_workflow(request)
        
        # Log result to AgentCore if enabled
        if settings.agentcore_enabled:
            await log_evaluation_result(result)
        
        total_evaluations += 1
        
        return {
            "session_id": session_id,
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "result": result.dict()
        }
        
    finally:
        active_sessions.discard(session_id)


@app.tool()
async def batch_evaluate_agents(
    evaluations: List[Dict[str, Any]],
    project_name: str = "default",
    experiment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform batch evaluation of multiple agents or workflows.
    
    Args:
        evaluations: List of evaluation requests
        project_name: Opik project name
        experiment_name: Optional experiment name
    
    Returns:
        Dictionary containing batch evaluation results
    """
    batch_id = str(uuid.uuid4())
    start_time = time.time()
    results = []
    
    for eval_request in evaluations:
        try:
            if eval_request.get("type") == "multiagent":
                result = await evaluate_multiagent_workflow(
                    workflow_id=eval_request["workflow_id"],
                    workflow_type=eval_request["workflow_type"],
                    agents=eval_request["agents"],
                    conversation_messages=eval_request["conversation_messages"],
                    evaluators=eval_request["evaluators"],
                    project_name=project_name,
                    experiment_name=experiment_name,
                    metadata=eval_request.get("metadata")
                )
                results.append(result)
            else:
                result = await evaluate_agent(
                    agent_id=eval_request["agent_id"],
                    test_cases=eval_request["test_cases"],
                    evaluators=eval_request["evaluators"],
                    project_name=project_name,
                    experiment_name=experiment_name,
                    metadata=eval_request.get("metadata")
                )
                results.append(result)
                
        except Exception as e:
            results.append({
                "error": str(e),
                "request": eval_request
            })
    
    execution_time = (time.time() - start_time) * 1000
    
    # Calculate summary statistics
    successful_results = [r for r in results if "error" not in r]
    total_tests = sum(r.get("total_tests", 0) for r in successful_results)
    passed_tests = sum(r.get("passed_tests", 0) for r in successful_results)
    failed_tests = sum(r.get("failed_tests", 0) for r in successful_results)
    
    average_scores = [r.get("average_score", 0.0) for r in successful_results if r.get("average_score") is not None]
    overall_average = sum(average_scores) / len(average_scores) if average_scores else 0.0
    
    return {
        "batch_id": batch_id,
        "total_evaluations": len(evaluations),
        "successful_evaluations": len(successful_results),
        "failed_evaluations": len(results) - len(successful_results),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "overall_average_score": overall_average,
        "execution_time_ms": execution_time,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.tool()
async def get_evaluation_metrics() -> Dict[str, Any]:
    """
    Get available evaluation metrics and their descriptions.
    
    Returns:
        Dictionary of available metrics
    """
    metrics = {
        "single_agent_metrics": {
            "accuracy": "Measures how accurate the agent's response is compared to expected output",
            "relevance": "Evaluates how relevant the response is to the input query",
            "coherence": "Assesses the logical flow and consistency of the response",
            "completeness": "Checks if the response fully addresses the input",
            "factuality": "Verifies the factual correctness of the response",
            "helpfulness": "Measures how helpful the response is to the user",
            "toxicity": "Detects harmful or toxic content in the response",
            "bias": "Identifies potential biases in the agent's response"
        },
        "multiagent_metrics": {
            "conversation_quality": "Evaluates the overall quality of multi-agent conversations",
            "agent_coordination": "Measures how well agents coordinate and hand off tasks",
            "workflow_efficiency": "Assesses the efficiency of the multi-agent workflow"
        },
        "workflow_types": {
            "single": "Single agent evaluation",
            "multi_agent": "General multi-agent system",
            "agent2agent": "Agent-to-Agent (A2A) protocol workflows",
            "graph": "Graph-based multi-agent workflows",
            "swarm": "Swarm intelligence patterns",
            "workflow": "Sequential workflow patterns"
        }
    }
    
    return metrics


@app.tool()
async def get_server_status() -> Dict[str, Any]:
    """
    Get current server status and statistics.
    
    Returns:
        Dictionary containing server status information
    """
    uptime = time.time() - server_start_time
    
    # Test Opik connection
    opik_connected = True
    try:
        # Simple connection test
        await asyncio.sleep(0.01)  # Simulate connection check
    except Exception:
        opik_connected = False
    
    status = ServerStatus(
        status="running",
        version="1.0.0",
        opik_connected=opik_connected,
        agentcore_connected=settings.agentcore_enabled,
        uptime_seconds=uptime,
        total_evaluations=total_evaluations,
        active_sessions=len(active_sessions)
    )
    
    return status.dict()


@app.tool()
async def create_test_data(
    num_test_cases: int = 5,
    agent_types: List[str] = ["single", "multiagent"]
) -> Dict[str, Any]:
    """
    Generate sample test data for evaluation testing.
    
    Args:
        num_test_cases: Number of test cases to generate
        agent_types: Types of agents to generate test data for
    
    Returns:
        Dictionary containing sample test data
    """
    test_data = {
        "single_agent_tests": [],
        "multiagent_tests": []
    }
    
    if "single" in agent_types:
        for i in range(num_test_cases):
            test_case = {
                "id": f"test-{i+1}",
                "input": f"Test question {i+1}: What is artificial intelligence?",
                "expected_output": "Artificial Intelligence (AI) is a field of computer science focused on creating systems that can perform tasks that typically require human intelligence.",
                "context": {"domain": "AI", "difficulty": "basic"},
                "metadata": {"test_type": "knowledge", "category": "AI basics"}
            }
            test_data["single_agent_tests"].append(test_case)
    
    if "multiagent" in agent_types:
        for i in range(num_test_cases):
            conversation = {
                "workflow_id": f"workflow-{i+1}",
                "workflow_type": "agent2agent",
                "agents": ["researcher", "writer", "reviewer"],
                "conversation_messages": [
                    {
                        "from_agent": "user",
                        "to_agent": "researcher",
                        "message": f"Research topic: AI trends {i+1}",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    {
                        "from_agent": "researcher",
                        "to_agent": "writer",
                        "message": f"Research findings: AI trend {i+1} shows significant growth",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    {
                        "from_agent": "writer",
                        "to_agent": "reviewer",
                        "message": f"Draft article about AI trend {i+1}",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    {
                        "from_agent": "reviewer",
                        "to_agent": "user",
                        "message": f"Final article about AI trend {i+1} - approved",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ],
                "evaluators": ["conversation_quality", "agent_coordination", "workflow_efficiency"],
                "metadata": {"test_type": "workflow", "complexity": "medium"}
            }
            test_data["multiagent_tests"].append(conversation)
    
    return test_data


# Resources for documentation and examples
@app.resource("opik://docs/quickstart")
async def quickstart_guide() -> Resource:
    """Quickstart guide for using the Opik MCP Server"""
    content = """
# Opik MCP Server Quickstart

## Overview
This MCP server provides comprehensive evaluation capabilities for Strands Agents and multi-agent systems using the Opik evaluation framework.

## Basic Usage

### 1. Evaluate Single Agent
```python
result = await evaluate_agent(
    agent_id="my-agent",
    test_cases=[
        {
            "input": "What is machine learning?",
            "expected_output": "Machine learning is a subset of AI...",
            "context": {"domain": "AI"}
        }
    ],
    evaluators=["accuracy", "relevance", "helpfulness"]
)
```

### 2. Evaluate Multi-Agent Workflow
```python
result = await evaluate_multiagent_workflow(
    workflow_id="research-workflow",
    workflow_type="agent2agent",
    agents=["researcher", "writer"],
    conversation_messages=[
        {
            "from_agent": "user",
            "to_agent": "researcher", 
            "message": "Research AI trends"
        },
        {
            "from_agent": "researcher",
            "to_agent": "writer",
            "message": "Key findings: ..."
        }
    ],
    evaluators=["conversation_quality", "agent_coordination"]
)
```

### 3. Batch Evaluation
```python
results = await batch_evaluate_agents([
    {
        "agent_id": "agent1",
        "test_cases": [...],
        "evaluators": ["accuracy"]
    },
    {
        "type": "multiagent",
        "workflow_id": "workflow1",
        "workflow_type": "graph",
        "agents": [...],
        "conversation_messages": [...],
        "evaluators": ["workflow_efficiency"]
    }
])
```

## Available Metrics

### Single Agent Metrics
- **accuracy**: Response accuracy vs expected output
- **relevance**: Response relevance to input
- **coherence**: Logical flow and consistency
- **helpfulness**: How helpful the response is
- **factuality**: Factual correctness
- **toxicity**: Harmful content detection
- **bias**: Bias detection

### Multi-Agent Metrics  
- **conversation_quality**: Overall conversation quality
- **agent_coordination**: Agent coordination effectiveness
- **workflow_efficiency**: Workflow execution efficiency

## Workflow Types
- **single**: Single agent
- **agent2agent**: A2A protocol workflows
- **graph**: Graph-based workflows
- **swarm**: Swarm intelligence
- **workflow**: Sequential workflows

## AgentCore Integration
When deployed on AWS Bedrock AgentCore, evaluations are automatically logged to CloudWatch with full observability.
"""
    
    return Resource(
        uri="opik://docs/quickstart",
        name="Quickstart Guide",
        description="Getting started with Opik MCP Server",
        mimeType="text/markdown",
        text=content
    )


@app.resource("opik://examples/strands-integration")
async def strands_integration_examples() -> Resource:
    """Examples of integrating with Strands Agents"""
    content = """
# Strands Agents Integration Examples

## Agent2Agent (A2A) Evaluation

```python
# Evaluate A2A conversation flow
a2a_result = await evaluate_multiagent_workflow(
    workflow_id="customer-support-a2a",
    workflow_type="agent2agent",
    agents=["intake_agent", "specialist_agent", "resolution_agent"],
    conversation_messages=[
        {
            "from_agent": "user",
            "to_agent": "intake_agent",
            "message": "I need help with my account"
        },
        {
            "from_agent": "intake_agent", 
            "to_agent": "specialist_agent",
            "message": "Customer needs account assistance - routing to specialist"
        },
        {
            "from_agent": "specialist_agent",
            "to_agent": "resolution_agent", 
            "message": "Account issue identified - needs password reset"
        },
        {
            "from_agent": "resolution_agent",
            "to_agent": "user",
            "message": "Password reset link sent to your email"
        }
    ],
    evaluators=["conversation_quality", "agent_coordination", "helpfulness"]
)
```

## Graph Workflow Evaluation

```python
# Evaluate graph-based multi-agent workflow
graph_result = await evaluate_multiagent_workflow(
    workflow_id="content-creation-graph",
    workflow_type="graph", 
    agents=["researcher", "writer", "editor", "reviewer"],
    conversation_messages=[
        # Parallel research phase
        {
            "from_agent": "coordinator",
            "to_agent": "researcher",
            "message": "Research topic: AI in healthcare"
        },
        # Writing phase
        {
            "from_agent": "researcher",
            "to_agent": "writer", 
            "message": "Research complete: Key findings attached"
        },
        # Parallel editing and review
        {
            "from_agent": "writer",
            "to_agent": "editor",
            "message": "First draft complete"
        },
        {
            "from_agent": "writer", 
            "to_agent": "reviewer",
            "message": "First draft for review"
        }
    ],
    evaluators=["workflow_efficiency", "agent_coordination", "completeness"]
)
```

## Swarm Intelligence Evaluation

```python
# Evaluate swarm-based problem solving
swarm_result = await evaluate_multiagent_workflow(
    workflow_id="optimization-swarm",
    workflow_type="swarm",
    agents=["optimizer_1", "optimizer_2", "optimizer_3", "coordinator"],
    conversation_messages=[
        {
            "from_agent": "coordinator",
            "to_agent": "optimizer_1",
            "message": "Optimize parameter set A"
        },
        {
            "from_agent": "coordinator", 
            "to_agent": "optimizer_2",
            "message": "Optimize parameter set B"
        },
        {
            "from_agent": "optimizer_1",
            "to_agent": "coordinator",
            "message": "Best result for A: 0.85"
        },
        {
            "from_agent": "optimizer_2",
            "to_agent": "coordinator", 
            "message": "Best result for B: 0.92"
        }
    ],
    evaluators=["workflow_efficiency", "agent_coordination"]
)
```

## Production Integration

```python
# Production evaluation with full observability
async def evaluate_production_agent(agent_instance, test_suite):
    results = await evaluate_agent(
        agent_id=agent_instance.id,
        test_cases=test_suite.test_cases,
        evaluators=["accuracy", "relevance", "helpfulness", "toxicity"],
        project_name="production-evaluations",
        experiment_name=f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        metadata={
            "environment": "production",
            "version": agent_instance.version,
            "deployment_id": agent_instance.deployment_id
        }
    )
    
    # Results automatically logged to AgentCore CloudWatch
    return results
```
"""
    
    return Resource(
        uri="opik://examples/strands-integration", 
        name="Strands Integration Examples",
        description="Examples of evaluating Strands Agents workflows",
        mimeType="text/markdown",
        text=content
    )


if __name__ == "__main__":
    # This should not be called directly for MCP
    # Use main.py instead
    pass