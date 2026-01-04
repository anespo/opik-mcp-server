# Real Testing Guide - Opik MCP Server on AWS AgentCore

This guide explains how to test the Opik MCP Server and verify traces appear in both Opik platform and AWS observability.

## LLM Evaluation Model

The evaluators use **Claude 3.5 Sonnet** via Amazon Bedrock:
- Model ID: `eu.anthropic.claude-3-5-sonnet-20240620-v1:0` (EU inference profile)
- Region: `eu-west-1` (configurable)
- All 7 evaluation metrics use real LLM-based scoring

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Opik API key** set in environment
3. **AgentCore runtime deployed** and running

## Environment Setup

```bash
# Set required environment variables
export AWS_REGION="eu-west-1"
export OPIK_API_KEY="your-opik-api-key"
export OPIK_WORKSPACE="your-workspace"
export AGENTCORE_RUNTIME_ARN="arn:aws:bedrock-agentcore:eu-west-1:YOUR_ACCOUNT:runtime/opik_mcp_server-XXXXX"
```

## Testing Methods

### Method 1: Local Testing (No AgentCore Required)

Test the LLM evaluators directly without deploying to AgentCore:

```bash
cd yourlocaldirectory/opik-mcp-agentcore
python scripts/test-real-traces.py
```

If `AGENTCORE_RUNTIME_ARN` is not set, the script runs in local mode and tests the evaluators directly against Bedrock.

### Method 2: Test via Kiro IDE

1. Copy `kiro-integration/mcp.json` to your Kiro settings
2. Use the MCP tools directly in Kiro chat:

```
# Test single agent evaluation
Use the evaluate_agent tool with:
- agent_id: "test-agent"
- test_cases: [{"input": "What is AWS?", "expected_output": "AWS is Amazon Web Services"}]
- evaluators: ["accuracy", "relevance"]
```

### Method 3: Test Deployed AgentCore Runtime

```bash
# Set your runtime ARN
export AGENTCORE_RUNTIME_ARN="your-runtime-arn"

# Run the test script
python scripts/test-real-traces.py
```

### Method 4: Direct AWS CLI Invocation

```bash
# Invoke the deployed MCP server
aws bedrock-agentcore-runtime invoke \
  --runtime-arn "$AGENTCORE_RUNTIME_ARN" \
  --payload '{"tool":"evaluate_agent","arguments":{"agent_id":"test","test_cases":[{"input":"Hello","expected_output":"Hi"}],"evaluators":["accuracy"]}}' \
  --region eu-west-1 \
  output.json

cat output.json
```

## Verifying Traces

### 1. Opik Platform

1. Go to [https://www.comet.com/opik](https://www.comet.com/opik)
2. Navigate to your workspace
3. Check the "Traces" section for evaluation traces
4. Look for projects named `opik-mcp-test` or your custom project name

### 2. AWS CloudWatch Logs

```bash
# View recent logs
aws logs tail /aws/bedrock-agentcore/opik-evaluations --follow --region eu-west-1
```

Or via console:
- Go to CloudWatch → Log groups → `/aws/bedrock-agentcore/opik-evaluations`

### 3. AWS X-Ray Traces

- Go to X-Ray → Traces in AWS Console
- Filter by service name: `opik-mcp-server`
- View trace details and latency

## Available Evaluation Metrics

All metrics use Claude 3.5 Sonnet for LLM-based evaluation:

| Metric | Description | Use Case |
|--------|-------------|----------|
| `accuracy` | Factual correctness vs expected output | Single agent |
| `relevance` | Response relevance to query | Single agent |
| `coherence` | Logical structure and clarity | Single agent |
| `helpfulness` | Actionable and useful response | Single agent |
| `conversation_quality` | Multi-turn conversation quality | Multi-agent |
| `agent_coordination` | Agent handoff effectiveness | Multi-agent |
| `workflow_efficiency` | Workflow optimization | Multi-agent |

## Example Test Cases

### Single Agent Evaluation

```python
{
    "tool": "evaluate_agent",
    "arguments": {
        "agent_id": "customer-service-bot",
        "test_cases": [
            {
                "input": "How do I reset my password?",
                "expected_output": "Click 'Forgot Password' on the login page",
                "context": {"category": "account"}
            }
        ],
        "evaluators": ["accuracy", "helpfulness", "relevance"],
        "project_name": "customer-service-eval"
    }
}
```

### Multi-Agent Workflow Evaluation

```python
{
    "tool": "evaluate_multiagent_workflow",
    "arguments": {
        "workflow_id": "support-workflow-001",
        "workflow_type": "agent2agent",
        "agents": ["triage", "specialist", "resolver"],
        "conversation_messages": [
            {"from_agent": "triage", "to_agent": "specialist", "message": "User needs billing help"},
            {"from_agent": "specialist", "to_agent": "resolver", "message": "Issue identified: duplicate charge"},
            {"from_agent": "resolver", "to_agent": "triage", "message": "Refund processed successfully"}
        ],
        "evaluators": ["conversation_quality", "agent_coordination", "workflow_efficiency"],
        "project_name": "support-workflow-eval"
    }
}
```

## Troubleshooting

### No traces in Opik

1. Verify `OPIK_API_KEY` is correct
2. Check the workspace name matches
3. Ensure the MCP server has network access to Opik API

### No traces in CloudWatch

1. Verify IAM permissions include `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:TagResource`
2. Check the log group exists: `/aws/bedrock-agentcore/opik-evaluations`
3. Verify AgentCore runtime is running

### LLM evaluation errors

1. Verify Bedrock access for Claude 3.5 Sonnet in your region
2. Check IAM permissions include `bedrock:InvokeModel`
3. Ensure the model ID is correct: `eu.anthropic.claude-3-5-sonnet-20240620-v1:0`

### AgentCore invocation fails

1. Check runtime status: `aws bedrock-agentcore describe-runtime --runtime-arn $AGENTCORE_RUNTIME_ARN`
2. Verify IAM permissions for `bedrock-agentcore-runtime:Invoke`
3. Check runtime logs in CloudWatch

## Performance Notes

- LLM evaluation adds ~1-3 seconds per metric (Claude API call)
- Batch evaluations run metrics in parallel where possible
- Consider using fewer metrics for faster feedback during development
