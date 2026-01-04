#!/bin/bash

# Sanitize project files for GitHub repository
# Removes sensitive information and replaces with placeholders

set -e

echo "🧹 Sanitizing project files for GitHub repository..."

# Create backup
echo "📋 Creating backup..."
cp -r . ../opik-mcp-server-backup

# Files to sanitize
FILES_TO_SANITIZE=(
    ".env.example"
    ".bedrock_agentcore.yaml"
    "scripts/deploy.sh"
    "scripts/fix-iam-permissions.sh"
    "scripts/iam-policy-fix.json"
    "kiro-integration/mcp.json"
    "TESTING_GUIDE.md"
    "DEPLOYMENT.md"
    "README.md"
)

# Sanitization patterns
declare -A REPLACEMENTS=(
    ["025073416907"]="YOUR_AWS_ACCOUNT_ID"
    ["eu-west-1"]="YOUR_AWS_REGION"
    ["/Users/anespo28gmail.com"]="yourlocaldirectory"
    ["anespo28gmail.com"]="yourusername"
    ["HSUAK9vFPSkqp3y0REqn2X0coY"]="YOUR_OPIK_API_KEY"
    ["arn:aws:iam::025073416907:role/AmazonBedrockAgentCoreSDKRuntime-eu-west-1-aba5468885"]="arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/AmazonBedrockAgentCoreSDKRuntime-YOUR_AWS_REGION-XXXXX"
    ["arn:aws:bedrock-agentcore:eu-west-1:025073416907:runtime/opik_mcp_server-SKTEQX3Omg"]="arn:aws:bedrock-agentcore:YOUR_AWS_REGION:YOUR_AWS_ACCOUNT_ID:runtime/opik_mcp_server-XXXXX"
    ["025073416907.dkr.ecr.eu-west-1.amazonaws.com"]="YOUR_AWS_ACCOUNT_ID.dkr.ecr.YOUR_AWS_REGION.amazonaws.com"
    ["opik_mcp_server-SKTEQX3Omg"]="opik_mcp_server-XXXXX"
    ["opik_mcp_server_mem-d22jGQH6ii"]="opik_mcp_server_mem-XXXXX"
    ["bedrock-agentcore-opik_mcp_server-builder"]="bedrock-agentcore-opik_mcp_server-builder"
)

# Function to sanitize a file
sanitize_file() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "🔧 Sanitizing: $file"
        
        # Create temporary file
        local temp_file=$(mktemp)
        cp "$file" "$temp_file"
        
        # Apply replacements
        for pattern in "${!REPLACEMENTS[@]}"; do
            replacement="${REPLACEMENTS[$pattern]}"
            sed -i.bak "s|$pattern|$replacement|g" "$temp_file"
        done
        
        # Move sanitized file back
        mv "$temp_file" "$file"
        
        # Remove backup
        rm -f "${file}.bak"
        
        echo "✅ Sanitized: $file"
    else
        echo "⚠️  File not found: $file"
    fi
}

# Sanitize each file
for file in "${FILES_TO_SANITIZE[@]}"; do
    sanitize_file "$file"
done

# Remove sensitive files
echo "🗑️  Removing sensitive files..."
rm -f .env
rm -f uv.lock
rm -rf .venv
rm -rf __pycache__
rm -rf src/opik_mcp_server/__pycache__
rm -rf .pytest_cache

# Create .gitignore
echo "📝 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Environment files
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# UV
uv.lock

# Logs
*.log

# AWS
.aws/

# Temporary files
*.tmp
*.temp

# Generated diagrams (optional - you may want to keep these)
generated-diagrams/

# Backup files
*-backup/
EOF

echo "✅ Project sanitized successfully!"
echo ""
echo "📊 Summary:"
echo "   - Sanitized ${#FILES_TO_SANITIZE[@]} files"
echo "   - Removed sensitive information"
echo "   - Created .gitignore"
echo "   - Backup created at ../opik-mcp-server-backup"
echo ""
echo "🚀 Ready for GitHub repository!"
echo ""
echo "💡 Next steps:"
echo "   1. Review sanitized files"
echo "   2. Initialize git repository: git init"
echo "   3. Add files: git add ."
echo "   4. Commit: git commit -m 'Initial commit: Opik MCP Server for AWS AgentCore'"
echo "   5. Push to GitHub"
echo ""