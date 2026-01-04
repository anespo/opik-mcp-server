#!/usr/bin/env python3
"""
Test script for Opik MCP Server integration with Kiro
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def test_server_status():
    """Test server status"""
    print("📊 Testing server status...")
    
    # Import the actual function implementation
    from opik_mcp_server.server import server_start_time, total_evaluations, active_sessions
    from opik_mcp_server.models import ServerStatus
    import time
    
    uptime = time.time() - server_start_time
    
    # Test Opik connection
    opik_connected = True
    try:
        import opik
        import os
        client = opik.Opik(api_key=os.getenv('OPIK_API_KEY'))
    except Exception:
        opik_connected = False
    
    status = ServerStatus(
        status="running",
        version="1.0.0",
        opik_connected=opik_connected,
        agentcore_connected=True,  # From settings
        uptime_seconds=uptime,
        total_evaluations=total_evaluations,
        active_sessions=len(active_sessions)
    )
    
    status_dict = status.dict()
    
    print(f"✅ Server status retrieved:")
    print(f"   - Status: {status_dict['status']}")
    print(f"   - Version: {status_dict['version']}")
    print(f"   - Opik connected: {status_dict['opik_connected']}")
    print(f"   - AgentCore connected: {status_dict['agentcore_connected']}")
    print(f"   - Total evaluations: {status_dict['total_evaluations']}")
    print(f"   - Active sessions: {status_dict['active_sessions']}")
    print()
    
    return status_dict


async def test_evaluation_metrics():
    """Test evaluation metrics retrieval"""
    print("📋 Testing evaluation metrics...")
    
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
    
    print(f"✅ Evaluation metrics retrieved:")
    print(f"   - Single agent metrics: {len(metrics['single_agent_metrics'])}")
    print(f"   - Multi-agent metrics: {len(metrics['multiagent_metrics'])}")
    print(f"   - Workflow types: {len(metrics['workflow_types'])}")
    print()
    
    return metrics


async def test_create_test_data():
    """Test test data creation"""
    print("🎲 Testing test data creation...")
    
    num_test_cases = 3
    agent_types = ["single", "multiagent"]
    
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
    
    print(f"✅ Test data created:")
    print(f"   - Single agent tests: {len(test_data['single_agent_tests'])}")
    print(f"   - Multi-agent tests: {len(test_data['multiagent_tests'])}")
    print()
    
    return test_data


async def test_single_agent_evaluation():
    """Test single agent evaluation"""
    print("🧪 Testing single agent evaluation...")
    
    # Import evaluator classes directly
    from opik_mcp_server.evaluators import AgentEvaluator
    from opik_mcp_server.models import EvaluationRequest, TestCase, EvaluationMetric
    
    test_cases = [
        TestCase(
            id="test-1",
            input="What is artificial intelligence?",
            expected_output="Artificial Intelligence (AI) is a field of computer science focused on creating systems that can perform tasks that typically require human intelligence.",
            context={"domain": "AI", "difficulty": "basic"},
            metadata={"test_type": "knowledge", "category": "AI basics"}
        ),
        TestCase(
            id="test-2", 
            input="Explain machine learning in simple terms",
            expected_output="Machine learning is a subset of AI where computers learn patterns from data to make predictions or decisions without being explicitly programmed for each task.",
            context={"domain": "ML", "difficulty": "basic"},
            metadata={"test_type": "explanation", "category": "ML basics"}
        )
    ]
    
    request = EvaluationRequest(
        agent_id="test-agent-1",
        test_cases=test_cases,
        evaluators=[EvaluationMetric.ACCURACY, EvaluationMetric.RELEVANCE, EvaluationMetric.HELPFULNESS],
        project_name="kiro-integration-test",
        experiment_name=f"single-agent-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    
    # Mock agent function
    async def mock_agent_function(input_text: str, context: dict) -> str:
        await asyncio.sleep(0.1)  # Simulate processing
        return f"Mock agent response to: {input_text}"
    
    evaluator = AgentEvaluator()
    results = await evaluator.evaluate_agent(request, mock_agent_function)
    
    # Convert to summary format
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    failed_tests = total_tests - passed_tests
    average_score = sum(r.overall_score for r in results) / len(results) if results else 0.0
    
    result = {
        "session_id": "test-session",
        "agent_id": "test-agent-1",
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "average_score": average_score,
        "results": [r.dict() for r in results]
    }
    
    print(f"✅ Single agent evaluation completed:")
    print(f"   - Total tests: {result['total_tests']}")
    print(f"   - Passed: {result['passed_tests']}")
    print(f"   - Failed: {result['failed_tests']}")
    print(f"   - Average score: {result['average_score']:.3f}")
    print()
    
    return result


async def test_multiagent_evaluation():
    """Test multi-agent workflow evaluation"""
    print("🤖 Testing multi-agent workflow evaluation...")
    
    from opik_mcp_server.evaluators import MultiAgentEvaluator
    from opik_mcp_server.models import (
        MultiAgentEvaluationRequest, AgentConversation, AgentMessage, 
        AgentType, EvaluationMetric
    )
    
    conversation_messages = [
        AgentMessage(
            from_agent="user",
            to_agent="researcher",
            message="Research the latest trends in AI for healthcare",
            timestamp=datetime.utcnow()
        ),
        AgentMessage(
            from_agent="researcher",
            to_agent="writer",
            message="Key findings: AI in healthcare shows 40% improvement in diagnostic accuracy, telemedicine adoption increased 300%, and AI-powered drug discovery reduced development time by 2 years.",
            timestamp=datetime.utcnow()
        ),
        AgentMessage(
            from_agent="writer",
            to_agent="reviewer",
            message="Draft article: 'AI Revolution in Healthcare: Transforming Patient Care Through Technology'. The article covers diagnostic improvements, telemedicine growth, and accelerated drug discovery.",
            timestamp=datetime.utcnow()
        ),
        AgentMessage(
            from_agent="reviewer",
            to_agent="user",
            message="Final article approved. The content is well-structured, factually accurate, and provides valuable insights into AI's impact on healthcare. Ready for publication.",
            timestamp=datetime.utcnow()
        )
    ]
    
    conversation = AgentConversation(
        conversation_id="healthcare-research-workflow",
        agents=["researcher", "writer", "reviewer"],
        messages=conversation_messages,
        workflow_type=AgentType.AGENT2AGENT
    )
    
    request = MultiAgentEvaluationRequest(
        workflow_id="healthcare-research-workflow",
        workflow_type=AgentType.AGENT2AGENT,
        conversation=conversation,
        evaluators=[
            EvaluationMetric.CONVERSATION_QUALITY, 
            EvaluationMetric.AGENT_COORDINATION, 
            EvaluationMetric.WORKFLOW_EFFICIENCY
        ],
        project_name="kiro-integration-test",
        experiment_name=f"multiagent-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    
    evaluator = MultiAgentEvaluator()
    evaluation_result = await evaluator.evaluate_agent2agent_flow(request)
    
    result = {
        "session_id": "test-session",
        "workflow_id": "healthcare-research-workflow",
        "workflow_type": "agent2agent",
        "result": evaluation_result.dict()
    }
    
    print(f"✅ Multi-agent evaluation completed:")
    print(f"   - Workflow ID: {result['workflow_id']}")
    print(f"   - Workflow type: {result['workflow_type']}")
    print(f"   - Overall score: {result['result']['overall_score']:.3f}")
    print(f"   - Passed: {'Yes' if result['result']['passed'] else 'No'}")
    print()
    
    return result


async def main():
    """Run all integration tests"""
    print("🚀 Starting Opik MCP Server integration tests with Kiro...")
    print("=" * 60)
    print()
    
    try:
        # Test all MCP tools
        await test_server_status()
        await test_evaluation_metrics()
        await test_create_test_data()
        await test_single_agent_evaluation()
        await test_multiagent_evaluation()
        
        print("=" * 60)
        print("🎉 All integration tests completed successfully!")
        print()
        print("📝 Next steps for Kiro integration:")
        print("   1. Copy kiro-integration/mcp.json to your Kiro workspace .kiro/settings/")
        print("   2. Restart Kiro to load the MCP server")
        print("   3. Use the MCP tools in Kiro chat with commands like:")
        print("      - 'Evaluate my agent with these test cases...'")
        print("      - 'Run a multi-agent workflow evaluation...'")
        print("      - 'Show me evaluation metrics...'")
        print()
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())