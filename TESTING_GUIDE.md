# Testing Guide: Opik MCP Server with Kiro and Real Traces

## Prerequisites

1. **Kiro IDE** installed and configured
2. **AWS CLI** configured with appropriate permissions
3. **Opik API Key** configured
4. **AgentCore deployment** completed

## Step 1: Configure Kiro MCP Integration

1. Copy the MCP configuration to Kiro:
```bash
cp kiro-integration/mcp.json ~/.kiro/settings/
```

2. Restart Kiro IDE to load the MCP server

3. Verify MCP server is loaded in Kiro's MCP panel

## Step 2: Test Single Agent Evaluation

In Kiro chat, run:

```
Evaluate my Strands customer service agent with accuracy and relevance metrics using these test cases:

Test Case 1:
- Input: "I need help with my order #12345. It hasn't arrived yet."
- Expected: "I understand your concern about order #12345. Let me check the status for you."
- Context: Customer service scenario - order inquiry

Test Case 2:
- Input: "Can you help me return a defective product?"
- Expected: "I'd be happy to help you with the return process."
- Context: Customer service scenario - product return
```

## Step 3: Test Multi-Agent Workflow

In Kiro chat, run:

```
Evaluate this Agent2Agent workflow with conversation quality and coordination metrics:

Agents: customer-intake-agent, technical-support-agent, escalation-manager-agent

Conversation:
1. customer-intake-agent → technical-support-agent: "Customer reports login issues with premium account PREM-12345"
2. technical-support-agent → customer-intake-agent: "Server outage identified, ETA 30 minutes"
3. customer-intake-agent → escalation-manager-agent: "Customer requesting compensation for 2+ hour outage"
```

## Step 4: Verify Real Traces in AWS

### CloudWatch Logs
```bash
# View AgentCore runtime logs
aws logs tail /aws/bedrock-agentcore/runtimes/opik_mcp_server-SKTEQX3Omg-DEFAULT --follow

# View evaluation logs
aws logs tail /aws/bedrock-agentcore/opik-evaluations --follow
```

### CloudWatch Metrics
1. Open AWS Console → CloudWatch → Metrics
2. Navigate to "OpikMCP" namespace
3. View metrics:
   - `OpikMCP/Evaluations/EvaluationScore`
   - `OpikMCP/Evaluations/EvaluationCount`
   - `OpikMCP/BatchEvaluations/BatchSuccessRate`

### X-Ray Traces
1. Open AWS Console → X-Ray → Traces
2. Filter by service: `opik-mcp-server`
3. View trace details for evaluation requests

### AgentCore Observability Dashboard
Visit: https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#gen-ai-observability/agent-core

## Step 5: Verify Traces in Opik Platform

1. Login to Opik: https://www.comet.com/opik
2. Navigate to your workspace
3. Check projects:
   - `strands-agents-evaluation`
   - `customer-service-agent-test`
4. View trace details, metrics, and evaluation results

## Expected Results

### Single Agent Evaluation
- **Accuracy**: 15-25% (indicates need for improvement)
- **Relevance**: 90-100% (good contextual understanding)
- **Helpfulness**: 50-70% (moderate helpfulness)

### Multi-Agent Workflow
- **Conversation Quality**: 90-100% (excellent communication)
- **Agent Coordination**: 90-100% (proper handoffs)
- **Workflow Efficiency**: 60-80% (room for optimization)

## Troubleshooting

### No Traces in CloudWatch
- Check IAM permissions for the execution role
- Verify log group exists: `/aws/bedrock-agentcore/opik-evaluations`
- Check AgentCore deployment status

### No Traces in Opik
- Verify Opik API key is correct
- Check network connectivity to Opik platform
- Review evaluation logs for API errors

### MCP Tools Not Available in Kiro
- Verify MCP configuration in `~/.kiro/settings/mcp.json`
- Restart Kiro IDE
- Check MCP server status in Kiro's MCP panel

## Advanced Testing

### Batch Evaluation
```
Run batch evaluation on multiple agents:
- Agent 1: customer-service-agent
- Agent 2: technical-support-agent  
- Agent 3: sales-agent

Use comprehensive metrics: accuracy, relevance, helpfulness, coherence
```

### Performance Testing
```
Evaluate agent performance under load:
- 50 concurrent evaluations
- Mixed single and multi-agent scenarios
- Monitor CloudWatch metrics for performance
```

## Monitoring and Alerts

### CloudWatch Alarms
- Evaluation failure rate > 10%
- Average evaluation time > 5 seconds
- Memory usage > 80%

### Custom Metrics
- Agent accuracy trends
- Multi-agent coordination scores
- Evaluation throughput

This testing approach ensures comprehensive validation of both the MCP server functionality and the observability integration across AWS and Opik platforms.