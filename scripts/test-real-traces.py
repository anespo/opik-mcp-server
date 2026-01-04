#!/usr/bin/env python3
"""
Test script to generate real traces in Opik and AWS AgentCore observability.
This script invokes the deployed MCP server to create actual evaluation traces.
"""

import json
import boto3
import time
import os
from datetime import datetime

# Configuration
REGION = os.environ.get("AWS_REGION", "eu-west-1")
RUNTIME_ARN = os.environ.get("AGENTCORE_RUNTIME_ARN", "")  # Set your runtime ARN

def get_agentcore_client():
    """Get AgentCore runtime client"""
    return boto3.client('bedrock-agentcore-runtime', region_name=REGION)

def invoke_evaluation(client, test_data: dict) -> dict:
    """Invoke the MCP server evaluation endpoint"""
    try:
        response = client.invoke(
            runtimeArn=RUNTIME_ARN,
            payload=json.dumps(test_data).encode('utf-8')
        )
        
        result = json.loads(response['body'].read())
        return result
    except Exception as e:
        print(f"Error invoking AgentCore: {e}")
        return {"error": str(e)}

def test_single_agent_evaluation():
    """Test single agent evaluation - generates traces"""
    print("\n" + "="*60)
    print("TEST 1: Single Agent Evaluation with Claude 3.5 Sonnet")
    print("="*60)
    
    test_data = {
        "tool": "evaluate_agent",
        "arguments": {
            "agent_id": "test-agent-001",
            "test_cases": [
                {
                    "input": "What is the capital of France?",
                    "expected_output": "The capital of France is Paris.",
                    "context": {"domain": "geography"}
                },
                {
                    "input": "Explain quantum computing in simple terms",
                    "expected_output": "Quantum computing uses quantum bits (qubits) that can exist in multiple states simultaneously, enabling parallel processing of complex calculations.",
                    "context": {"domain": "technology", "audience": "beginner"}
                },
                {
                    "input": "What are the benefits of cloud computing?",
                    "expected_output": "Cloud computing offers scalability, cost efficiency, flexibility, disaster recovery, and automatic updates.",
                    "context": {"domain": "technology"}
                }
            ],
            "evaluators": ["accuracy", "relevance", "helpfulness", "coherence"],
            "project_name": "opik-mcp-test",
            "experiment_name": f"single-agent-eval-{int(time.time())}"
        }
    }
    
    print(f"\nTest data: {json.dumps(test_data, indent=2)}")
    
    client = get_agentcore_client()
    result = invoke_evaluation(client, test_data)
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    return result

def test_multiagent_evaluation():
    """Test multi-agent workflow evaluation - generates traces"""
    print("\n" + "="*60)
    print("TEST 2: Multi-Agent Workflow Evaluation with Claude 3.5 Sonnet")
    print("="*60)
    
    test_data = {
        "tool": "evaluate_multiagent_workflow",
        "arguments": {
            "workflow_id": "workflow-001",
            "workflow_type": "agent2agent",
            "agents": ["coordinator", "researcher", "writer"],
            "conversation_messages": [
                {
                    "from_agent": "coordinator",
                    "to_agent": "researcher",
                    "message": "Please research the latest trends in AI agent development"
                },
                {
                    "from_agent": "researcher",
                    "to_agent": "coordinator",
                    "message": "Found key trends: multi-agent systems, tool use, and reasoning capabilities"
                },
                {
                    "from_agent": "coordinator",
                    "to_agent": "writer",
                    "message": "Create a summary based on the research findings"
                },
                {
                    "from_agent": "writer",
                    "to_agent": "coordinator",
                    "message": "Summary complete: AI agents are evolving with better coordination, tool integration, and reasoning"
                }
            ],
            "evaluators": ["conversation_quality", "agent_coordination", "workflow_efficiency"],
            "project_name": "opik-mcp-test",
            "experiment_name": f"multiagent-eval-{int(time.time())}"
        }
    }
    
    print(f"\nTest data: {json.dumps(test_data, indent=2)}")
    
    client = get_agentcore_client()
    result = invoke_evaluation(client, test_data)
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    return result

def test_batch_evaluation():
    """Test batch evaluation - generates multiple traces"""
    print("\n" + "="*60)
    print("TEST 3: Batch Evaluation with Claude 3.5 Sonnet")
    print("="*60)
    
    test_data = {
        "tool": "batch_evaluate_agents",
        "arguments": {
            "evaluations": [
                {
                    "agent_id": "customer-service-agent",
                    "test_cases": [
                        {
                            "input": "How do I reset my password?",
                            "expected_output": "To reset your password, click 'Forgot Password' on the login page and follow the email instructions.",
                            "context": {"category": "account"}
                        }
                    ],
                    "evaluators": ["accuracy", "helpfulness"]
                },
                {
                    "agent_id": "technical-support-agent",
                    "test_cases": [
                        {
                            "input": "My application is running slowly",
                            "expected_output": "Check CPU usage, memory consumption, and network latency. Consider scaling resources or optimizing code.",
                            "context": {"category": "performance"}
                        }
                    ],
                    "evaluators": ["relevance", "coherence"]
                }
            ],
            "project_name": "opik-mcp-test",
            "experiment_name": f"batch-eval-{int(time.time())}"
        }
    }
    
    print(f"\nTest data: {json.dumps(test_data, indent=2)}")
    
    client = get_agentcore_client()
    result = invoke_evaluation(client, test_data)
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    return result

def check_cloudwatch_logs():
    """Check CloudWatch logs for traces"""
    print("\n" + "="*60)
    print("Checking CloudWatch Logs")
    print("="*60)
    
    logs_client = boto3.client('logs', region_name=REGION)
    log_group = "/aws/bedrock-agentcore/opik-evaluations"
    
    try:
        # Get recent log streams
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        print(f"\nRecent log streams in {log_group}:")
        for stream in streams.get('logStreams', []):
            print(f"  - {stream['logStreamName']}")
            
            # Get recent events
            events = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream['logStreamName'],
                limit=10
            )
            
            for event in events.get('events', [])[:3]:
                timestamp = datetime.fromtimestamp(event['timestamp']/1000)
                print(f"    [{timestamp}] {event['message'][:100]}...")
                
    except Exception as e:
        print(f"Error checking logs: {e}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("OPIK MCP SERVER - REAL TRACE TESTING")
    print(f"Using Claude 3.5 Sonnet (eu.anthropic.claude-3-5-sonnet-20240620-v1:0)")
    print(f"Region: {REGION}")
    print(f"Runtime ARN: {RUNTIME_ARN or 'NOT SET - Please set AGENTCORE_RUNTIME_ARN'}")
    print("="*60)
    
    if not RUNTIME_ARN:
        print("\n⚠️  WARNING: AGENTCORE_RUNTIME_ARN not set!")
        print("Set it with: export AGENTCORE_RUNTIME_ARN='your-runtime-arn'")
        print("\nRunning in local test mode instead...")
        
        # Local test mode - test the evaluators directly
        import asyncio
        import sys
        sys.path.insert(0, 'src')
        
        from opik_mcp_server.evaluators import AccuracyMetric, RelevanceMetric
        
        async def test_local():
            print("\n--- Testing AccuracyMetric locally ---")
            metric = AccuracyMetric()
            
            input_data = {"input": "What is the capital of France?"}
            output_data = {"output": "The capital of France is Paris."}
            reference_data = {"expected_output": "Paris is the capital of France."}
            
            score, explanation = await metric.score(input_data, output_data, reference_data)
            print(f"Score: {score}")
            print(f"Explanation: {explanation}")
            
            print("\n--- Testing RelevanceMetric locally ---")
            relevance = RelevanceMetric()
            score2, explanation2 = await relevance.score(input_data, output_data, reference_data)
            print(f"Score: {score2}")
            print(f"Explanation: {explanation2}")
        
        asyncio.run(test_local())
        return
    
    # Run tests against deployed AgentCore
    results = []
    
    # Test 1: Single agent evaluation
    result1 = test_single_agent_evaluation()
    results.append(("Single Agent", result1))
    time.sleep(2)  # Allow traces to propagate
    
    # Test 2: Multi-agent evaluation
    result2 = test_multiagent_evaluation()
    results.append(("Multi-Agent", result2))
    time.sleep(2)
    
    # Test 3: Batch evaluation
    result3 = test_batch_evaluation()
    results.append(("Batch", result3))
    time.sleep(2)
    
    # Check CloudWatch logs
    check_cloudwatch_logs()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results:
        status = "✅ PASSED" if "error" not in result else "❌ FAILED"
        print(f"{name}: {status}")
    
    print("\n📊 Check traces at:")
    print("  - Opik: https://www.comet.com/opik")
    print(f"  - CloudWatch: https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#logsV2:log-groups/log-group/$252Faws$252Fbedrock-agentcore$252Fopik-evaluations")
    print(f"  - X-Ray: https://{REGION}.console.aws.amazon.com/xray/home?region={REGION}#/traces")

if __name__ == "__main__":
    main()
