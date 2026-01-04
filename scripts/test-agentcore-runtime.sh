#!/bin/bash

# Test the deployed AgentCore runtime to generate real traces
# This script tests the actual deployed MCP server, not local connections

set -e

echo "🧪 Testing Deployed AgentCore Runtime for Real Traces"
echo "======================================================"

# Check AgentCore status first
echo "📋 Checking AgentCore deployment status..."
agentcore status

echo ""
echo "🔍 Testing MCP server health through AgentCore..."

# Test 1: Health check through AgentCore
echo "Test 1: Health check"
agentcore invoke '{"method": "ping"}' || echo "⚠️  Ping test failed"

echo ""
echo "🧪 Test 2: Get evaluation metrics"
# This should work and generate traces
agentcore invoke '{
  "method": "tools/call",
  "params": {
    "name": "get_evaluation_metrics"
  }
}' || echo "⚠️  Get metrics test failed"

echo ""
echo "🧪 Test 3: Get server status"
agentcore invoke '{
  "method": "tools/call", 
  "params": {
    "name": "get_server_status"
  }
}' || echo "⚠️  Server status test failed"

echo ""
echo "🧪 Test 4: Simple agent evaluation"
agentcore invoke '{
  "method": "tools/call",
  "params": {
    "name": "evaluate_agent",
    "arguments": {
      "agent_id": "test-agent-via-agentcore",
      "test_cases": [
        {
          "input": "Hello, can you help me?",
          "expected_output": "Hello! I would be happy to help you.",
          "context": {"test": "agentcore_runtime"}
        }
      ],
      "evaluators": ["relevance"],
      "project_name": "agentcore-runtime-test",
      "metadata": {
        "test_type": "agentcore_invocation",
        "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
      }
    }
  }
}' || echo "⚠️  Agent evaluation test failed"

echo ""
echo "⏳ Waiting 30 seconds for traces to propagate..."
sleep 30

echo ""
echo "🔍 Checking for traces in AWS CloudWatch..."

# Check evaluation logs
echo "📋 Checking evaluation log group..."
aws logs describe-log-streams \
  --log-group-name "/aws/bedrock-agentcore/opik-evaluations" \
  --order-by LastEventTime \
  --descending \
  --max-items 5 || echo "⚠️  No evaluation log streams found"

# Check runtime logs for recent activity
echo ""
echo "📋 Checking AgentCore runtime logs (last 5 minutes)..."
aws logs tail \
  /aws/bedrock-agentcore/runtimes/opik_mcp_server-SKTEQX3Omg-DEFAULT \
  --since 5m | tail -20 || echo "⚠️  No recent runtime logs"

echo ""
echo "📊 Checking CloudWatch metrics..."
aws cloudwatch get-metric-statistics \
  --namespace "OpikMCP/Evaluations" \
  --metric-name "EvaluationCount" \
  --start-time $(date -d '1 hour ago' --iso-8601) \
  --end-time $(date --iso-8601) \
  --period 300 \
  --statistics Sum || echo "⚠️  No metrics found"

echo ""
echo "✅ Testing completed!"
echo ""
echo "💡 To verify traces:"
echo "   1. AWS CloudWatch: Check log groups and metrics"
echo "   2. Opik Platform: Check for 'agentcore-runtime-test' project"
echo "   3. X-Ray: Look for traces from opik-mcp-server service"
echo ""