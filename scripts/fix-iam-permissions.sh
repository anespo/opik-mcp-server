#!/bin/bash

# Fix IAM permissions for Opik MCP Server observability
# This script adds the necessary permissions to the AgentCore execution role

set -e

# Configuration
EXECUTION_ROLE_ARN="arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/AmazonBedrockAgentCoreSDKRuntime-YOUR_AWS_REGION-XXXXX"
EXECUTION_ROLE_NAME="AmazonBedrockAgentCoreSDKRuntime-YOUR_AWS_REGION-XXXXX"
POLICY_NAME="OpikMCPServerObservabilityPolicy"
POLICY_FILE="scripts/iam-policy-fix.json"

echo "🔧 Fixing IAM permissions for Opik MCP Server observability..."

# Check if policy file exists
if [ ! -f "$POLICY_FILE" ]; then
    echo "❌ Policy file not found: $POLICY_FILE"
    exit 1
fi

echo "📋 Policy file found: $POLICY_FILE"

# Create the IAM policy
echo "📝 Creating IAM policy: $POLICY_NAME"
POLICY_ARN=$(aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file://"$POLICY_FILE" \
    --description "Observability permissions for Opik MCP Server on AgentCore" \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || echo "")

if [ -z "$POLICY_ARN" ]; then
    echo "⚠️  Policy might already exist, trying to get existing policy ARN..."
    POLICY_ARN=$(aws iam list-policies \
        --scope Local \
        --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" \
        --output text)
    
    if [ -z "$POLICY_ARN" ]; then
        echo "❌ Failed to create or find policy: $POLICY_NAME"
        exit 1
    fi
    
    echo "📋 Found existing policy: $POLICY_ARN"
    
    # Update the existing policy with the latest version
    echo "🔄 Updating policy with latest permissions..."
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file://"$POLICY_FILE" \
        --set-as-default
    echo "✅ Policy updated successfully"
else
    echo "✅ Policy created successfully: $POLICY_ARN"
fi

# Attach the policy to the execution role
echo "🔗 Attaching policy to execution role: $EXECUTION_ROLE_NAME"
aws iam attach-role-policy \
    --role-name "$EXECUTION_ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

echo "✅ Policy attached successfully"

# Verify the attachment
echo "🔍 Verifying policy attachment..."
ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
    --role-name "$EXECUTION_ROLE_NAME" \
    --query "AttachedPolicies[?PolicyName=='$POLICY_NAME'].PolicyName" \
    --output text)

if [ "$ATTACHED_POLICIES" = "$POLICY_NAME" ]; then
    echo "✅ Policy attachment verified successfully"
else
    echo "❌ Policy attachment verification failed"
    exit 1
fi

echo ""
echo "🎉 IAM permissions fixed successfully!"
echo ""
echo "📊 Summary:"
echo "   Policy Name: $POLICY_NAME"
echo "   Policy ARN:  $POLICY_ARN"
echo "   Role Name:   $EXECUTION_ROLE_NAME"
echo ""
echo "🔄 The changes will take effect immediately."
echo "   You can now redeploy the agent to test the observability features."
echo ""
echo "💡 Next steps:"
echo "   1. Redeploy the agent: ./scripts/deploy.sh deploy"
echo "   2. Test evaluation through AgentCore runtime"
echo "   3. Check CloudWatch logs and X-Ray traces"
echo ""