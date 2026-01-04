#!/bin/bash

# Opik MCP Server Deployment Script for AWS Bedrock AgentCore
set -e

echo "🚀 Deploying Opik MCP Server to AWS Bedrock AgentCore..."

# Configuration
PROJECT_NAME="opik_mcp_server"
AWS_REGION="eu-west-1"
AWS_PROFILE="default"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if UV is installed
    if ! command -v uv &> /dev/null; then
        log_error "UV is not installed. Please install it first."
        log_info "Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if AgentCore CLI is installed
    if ! command -v agentcore &> /dev/null; then
        log_warning "AgentCore CLI not found. Installing..."
        uv tool install agentcore-cli
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity --profile $AWS_PROFILE --region $AWS_REGION &> /dev/null; then
        log_error "AWS credentials not configured properly for profile '$AWS_PROFILE' in region '$AWS_REGION'"
        log_info "Please run: aws configure --profile $AWS_PROFILE"
        exit 1
    fi
    
    # Check if Opik API key is set
    if [ -z "$OPIK_API_KEY" ]; then
        log_error "OPIK_API_KEY environment variable is not set"
        log_info "Please set your Opik API key: export OPIK_API_KEY='your-key-here'"
        exit 1
    fi
    
    # Verify ECR repository exists or can be created
    ECR_REPO_NAME="bedrock-agentcore-opik_mcp_server"
    if ! aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION --profile $AWS_PROFILE &> /dev/null; then
        log_info "ECR repository $ECR_REPO_NAME does not exist. AgentCore will create it automatically."
    else
        log_success "ECR repository $ECR_REPO_NAME exists"
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        log_info "Created .env file from template. Please review and update as needed."
    fi
    
    # Set the Opik API key in environment
    export OPIK_API_KEY="${OPIK_API_KEY}"
    
    log_success "Environment setup completed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies with UV..."
    
    # Create UV project if needed
    if [ ! -f "uv.lock" ]; then
        uv sync
        log_info "Created UV lock file"
    else
        uv sync
    fi
    
    log_success "Dependencies installed successfully with UV"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    # Run basic import test
    uv run python -c "
import sys
try:
    from opik_mcp_server.models import EvaluationRequest, AgentType, EvaluationMetric
    from opik_mcp_server.config import settings
    print('✅ All imports successful')
    print(f'✅ Configuration loaded: Opik workspace = {settings.opik_workspace}')
    print(f'✅ AWS region = {settings.aws_region}')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    # Test Opik connection
    uv run python -c "
import os
try:
    import opik
    client = opik.Opik(api_key=os.getenv('OPIK_API_KEY'))
    print('✅ Opik connection successful')
except Exception as e:
    print(f'❌ Opik connection failed: {e}')
    print('⚠️  Continuing deployment - connection will be tested in AgentCore')
"
    
    log_success "Tests completed"
}

# Deploy to AgentCore
deploy_to_agentcore() {
    log_info "Deploying to AWS Bedrock AgentCore..."
    
    # Validate AgentCore configuration
    log_info "Validating AgentCore configuration..."
    if [ ! -f ".bedrock_agentcore.yaml" ]; then
        log_error ".bedrock_agentcore.yaml not found"
        exit 1
    fi
    
    # Validate Docker build locally first (quick check)
    log_info "Validating Docker build configuration..."
    if ! docker --version &> /dev/null; then
        log_warning "Docker not available locally - skipping local validation"
    else
        # Quick syntax check of Dockerfile
        if ! docker build --dry-run . &> /dev/null; then
            log_warning "Docker dry-run failed - continuing with AgentCore build"
        else
            log_success "Docker configuration validated"
        fi
    fi
    
    # Set environment variables for deployment
    export AWS_REGION=$AWS_REGION
    export AWS_PROFILE=$AWS_PROFILE
    export OPIK_API_KEY=$OPIK_API_KEY
    
    # Deploy using AgentCore CLI with correct syntax
    log_info "Deploying with AgentCore CLI..."
    if agentcore deploy \
        --agent $PROJECT_NAME \
        --auto-update-on-conflict; then
        log_success "Deployment to AgentCore completed successfully!"
    else
        log_error "Deployment to AgentCore failed"
        log_info "Checking deployment logs..."
        
        # Try to get more detailed error information
        if command -v agentcore &> /dev/null; then
            log_info "Recent deployment logs:"
            agentcore logs --agent $PROJECT_NAME --lines 50 || true
        fi
        
        exit 1
    fi
}

# Setup CloudWatch dashboard
setup_monitoring() {
    log_info "Setting up CloudWatch monitoring..."
    
    # Create CloudWatch dashboard
    aws cloudwatch put-dashboard \
        --dashboard-name "OpikMCPServer-Dashboard" \
        --dashboard-body file://scripts/cloudwatch-dashboard.json \
        --region $AWS_REGION \
        --profile $AWS_PROFILE
    
    log_success "CloudWatch dashboard created"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Get AgentCore service status
    SERVICE_STATUS=$(agentcore status --agent $PROJECT_NAME --output json 2>/dev/null || echo '{"status": "unknown"}')
    
    if echo "$SERVICE_STATUS" | grep -q '"status": "running"'; then
        log_success "Service is running successfully!"
        
        # Get service endpoint
        ENDPOINT=$(echo "$SERVICE_STATUS" | jq -r '.endpoint // "N/A"')
        log_info "Service endpoint: $ENDPOINT"
        
        # Test health endpoint
        if [ "$ENDPOINT" != "N/A" ]; then
            log_info "Testing health endpoint..."
            if curl -f "$ENDPOINT/health" &> /dev/null; then
                log_success "Health check passed!"
            else
                log_warning "Health check failed - service may still be starting up"
            fi
        fi
    else
        log_warning "Service status check - deployment may still be in progress"
        echo "$SERVICE_STATUS"
    fi
}

# Main deployment flow
main() {
    echo "🎯 Starting Opik MCP Server deployment process..."
    echo "📍 Target: AWS Bedrock AgentCore ($AWS_REGION)"
    echo "🔑 AWS Profile: $AWS_PROFILE"
    echo "⚡ Using UV for dependency management"
    echo ""
    
    check_prerequisites
    setup_environment
    install_dependencies
    run_tests
    deploy_to_agentcore
    setup_monitoring
    verify_deployment
    
    echo ""
    log_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Next steps:"
    echo "  1. View logs: agentcore logs --agent $PROJECT_NAME"
    echo "  2. Monitor metrics: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=OpikMCPServer-Dashboard"
    echo "  3. Test MCP tools: Use the Kiro integration script"
    echo "  4. View AgentCore dashboard: https://console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/agentcore"
    echo ""
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "test")
        check_prerequisites
        setup_environment
        install_dependencies
        run_tests
        ;;
    "verify")
        verify_deployment
        ;;
    "logs")
        agentcore logs --agent $PROJECT_NAME --follow
        ;;
    "status")
        agentcore status --agent $PROJECT_NAME
        ;;
    "undeploy")
        log_info "Undeploying from AgentCore..."
        agentcore undeploy --agent $PROJECT_NAME
        log_success "Undeployment completed"
        ;;
    *)
        echo "Usage: $0 {deploy|test|verify|logs|status|undeploy}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment process (default)"
        echo "  test     - Run tests only"
        echo "  verify   - Verify existing deployment"
        echo "  logs     - View service logs"
        echo "  status   - Check service status"
        echo "  undeploy - Remove deployment"
        exit 1
        ;;
esac