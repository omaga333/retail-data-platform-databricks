#!/bin/bash
# Databricks Asset Bundle - Deployment Script
# Generated: 2026-07-02
# Bundle: retail-data-platform
# Target: dev

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      Deploying Retail Data Platform Asset Bundle            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to bundle root
cd /Workspace/Users/aajahhs712@gmail.com/Repos/aajahhs712@gmail.com/retail-data-platform-databricks

echo "📍 Current Directory: $(pwd)"
echo ""

# Validate first
echo "🔍 Step 1/3: Validating bundle configuration..."
databricks bundle validate --target dev

if [ $? -ne 0 ]; then
    echo "❌ Validation failed! Please fix errors before deploying."
    exit 1
fi

echo ""
echo "✅ Validation passed!"
echo ""

# Deploy
echo "🚀 Step 2/3: Deploying to development environment..."
echo "======================================================"
databricks bundle deploy --target dev

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed! Check the errors above."
    exit 1
fi

echo ""
echo "✅ Deployment completed successfully!"
echo ""

# Show next steps
echo "🎯 Step 3/3: Post-Deployment Actions"
echo "======================================"
echo ""
echo "✅ Resources created in your workspace:"
echo "   • Pipelines: Data Intelligence → Pipelines"
echo "   • Job: Workflows → Jobs → [dev] Retail Data Pipeline"
echo ""
echo "⚠️  IMPORTANT - Fix Salesforce OAuth:"
echo "   1. Navigate to: Catalog → Connections"
echo "   2. Find: sales_retail"
echo "   3. Click: Edit → Authenticate"
echo "   4. Login to Salesforce and authorize"
echo ""
echo "🚀 Ready to run? Execute:"
echo "   databricks bundle run retail_job --target dev"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎊 Deployment Complete! Your retail data platform is ready!"
echo "═══════════════════════════════════════════════════════════════"
