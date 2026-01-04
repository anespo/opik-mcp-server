# Opik MCP Server - Deployment Guide

This guide walks you through deploying the Opik MCP Server to AWS Bedrock AgentCore and integrating it with Kiro.

## Prerequisites

### 1. AWS Setup
- AWS CLI installed and configured
- AWS account with appropriate permissions
- Default profile configured for `eu-west-1` region
- Bedrock model access enabled for Claude 3.5 and Nova models

### 2. Opik Setup
- Opik account created at [comet.com](https://www.comet.com/opik)
- API key obtained: `HSUAK9vFPSkqp3y0REqn2X0coY`

### 3. Development Environment
- Python 3.11 or higher
- Git
- Virtual environment support

## Step 1: Build the Code

### Clone and Setup
```bash
# Navigate to the project
cd opik-mcp-server

# Initialize UV project
uv sync

# Install development dependencies
uv sync --dev
```

### Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Set your Opik API key
export OPIK_API_KEY="YOUR_OPIK_API_KEY"
```

### Verify Installation
```bash
# Test imports
uv run python -c "from opik_mcp_server import app; print('✅ Installation successful')"

# Test Opik connection
uv run python -c "
import opik
import os
client = opik.Opik(api_key=os.getenv('OPIK_API_KEY'))
print('✅ Opik connection successful')
"
```

## Step 2: Deploy to AgentCore

### Automated Deployment
```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Set environment variables
export OPIK_API_KEY="YOUR_OPIK_API_KEY"
export AWS_REGION="eu-west-1"
export AWS_PROFILE="default"

# Run full deployment
./scripts/deploy.sh deploy
```

### Manual Deployment Steps
If you prefer manual deployment:

```bash
# 1. Install AgentCore CLI
uv tool install agentcore-cli

# 2. Validate configuration
uv run agentcore validate --config agentcore.yaml

# 3. Deploy
uv run agentcore deploy \
    --config agentcore.yaml \
    --region eu-west-1 \
    --profile default \
    --wait \
    --timeout 600

# 4. Verify deployment
uv run agentcore status --name opik-mcp-server --region eu-west-1
```

### Deployment Verification
```bash
# Check service status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs

# Test health endpoint
curl -f "$(agentcore status --name opik-mcp-server --region eu-west-1 --output json | jq -r '.endpoint')/health"
```

## Step 3: Integrate with Kiro

### Setup MCP Configuration
```bash
# Copy MCP configuration to Kiro workspace
mkdir -p .kiro/settings
cp kiro-integration/mcp.json .kiro/settings/

# Or for global configuration
mkdir -p ~/.kiro/settings
cp kiro-integration/mcp.json ~/.kiro/settings/
```

### Test Integration
```bash
# Run integration tests
python kiro-integration/test-integration.py
```

### Kiro Usage Examples
Once integrated, you can use these commands in Kiro:

```
# Single agent evaluation
Evaluate my agent with test cases for accuracy and relevance

# Multi-agent workflow evaluation  
Evaluate this agent2agent conversation for coordination and efficiency

# Get available metrics
Show me all available evaluation metrics

# Create test data
Generate sample test data for evaluation
```

## Step 4: End-to-End Testing

### Local Testing
```bash
# Test all components locally
uv run pytest tests/ -v

# Test MCP server directly
uv run python -m opik_mcp_server.main &
SERVER_PID=$!

# Test MCP tools
uv run python kiro-integration/test-integration.py

# Cleanup
kill $SERVER_PID
```

### AgentCore Testing
```bash
# Test deployed service
./scripts/deploy.sh verify

# Run comprehensive tests
uv run agentcore test --name opik-mcp-server --region eu-west-1
```

### Integration Testing with Kiro
1. Open Kiro IDE
2. Verify MCP server is connected (check MCP panel)
3. Test evaluation commands in chat
4. Check CloudWatch logs for evaluation results

## Step 5: Architecture Diagram

### Generate Diagrams
```bash
# Install diagram dependencies (included in dev dependencies)
uv sync --dev

# Generate architecture diagrams
uv run python scripts/generate-architecture-diagram.py
```

This creates:
- `diagrams/opik_mcp_server_architecture_on_aws_agentcore.png`
- `diagrams/opik_mcp_server_evaluation_flow.png`

## Monitoring and Observability

### CloudWatch Dashboard
The deployment automatically creates a CloudWatch dashboard:
- **URL**: https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#dashboards:name=OpikMCPServer-Dashboard
- **Metrics**: Evaluation scores, pass/fail rates, execution times
- **Logs**: Detailed evaluation results and errors

### X-Ray Tracing
- **URL**: https://console.aws.amazon.com/xray/home?region=eu-west-1
- **Service Map**: Visual representation of service interactions
- **Traces**: Detailed execution traces for debugging

### Opik Dashboard
- **URL**: https://www.comet.com/opik
- **Projects**: View evaluation projects and experiments
- **Analytics**: Detailed evaluation analytics and trends

## Troubleshooting

### Common Issues

#### 1. Deployment Fails
```bash
# Check AWS credentials
aws sts get-caller-identity --profile default --region eu-west-1

# Check AgentCore CLI
agentcore --version

# Validate configuration
agentcore validate --config agentcore.yaml
```

#### 2. Opik Connection Issues
```bash
# Test Opik connection
uv run python -c "
import opik
import os
try:
    client = opik.Opik(api_key=os.getenv('OPIK_API_KEY'))
    print('✅ Connection successful')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

#### 3. Kiro Integration Issues
```bash
# Check MCP configuration
cat .kiro/settings/mcp.json

# Test MCP server locally
uv run python -m opik_mcp_server.main

# Check Kiro logs
# (Kiro menu > View > Developer > Toggle Developer Tools > Console)
```

#### 4. CloudWatch Logs Not Appearing
```bash
# Check log group exists
aws logs describe-log-groups \
    --log-group-name-prefix "/aws/bedrock-agentcore" \
    --region eu-west-1

# Check IAM permissions
aws iam get-role-policy \
    --role-name AgentCoreExecutionRole \
    --policy-name CloudWatchLogsPolicy \
    --region eu-west-1
```

### Getting Help
- **Logs**: `./scripts/deploy.sh logs`
- **Status**: `./scripts/deploy.sh status`
- **AWS Support**: Check AWS CloudWatch and X-Ray for detailed error information
- **Opik Support**: Check Opik dashboard for evaluation-specific issues

## Production Considerations

### Security
- Use IAM roles with minimal required permissions
- Enable VPC endpoints for private communication
- Rotate API keys regularly
- Enable CloudTrail for audit logging

### Performance
- Monitor CloudWatch metrics for performance bottlenecks
- Adjust AgentCore scaling parameters based on usage
- Use batch evaluations for high-volume scenarios
- Consider caching for frequently used evaluations

### Cost Optimization
- Set appropriate X-Ray sampling rates (default: 10%)
- Use CloudWatch log retention policies
- Monitor Bedrock model usage costs
- Consider Reserved Instances for consistent workloads

### Maintenance
- Regular dependency updates
- Monitor security advisories
- Backup evaluation data and configurations
- Test disaster recovery procedures

## Next Steps

1. **Blog Post**: Use the generated architecture diagrams in your AWS blog post
2. **Production Deployment**: Deploy to production environment with appropriate security controls
3. **Client Integration**: Integrate with your client's AI agent workflows
4. **Monitoring**: Set up alerts and monitoring for production usage
5. **Documentation**: Create client-specific documentation and training materials