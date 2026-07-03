# Deployment Guide - Retail Data Platform

This guide walks you through deploying the Retail Data Platform Databricks Asset Bundle to different environments.

## Prerequisites

### 1. Databricks CLI

Install the latest Databricks CLI:
```bash
pip install --upgrade databricks-cli
databricks --version  # Should be >= 0.218.0
```

### 2. Workspace Configuration

```bash
databricks configure
```

Provide:
- **Host:** `https://your-workspace.cloud.databricks.com`
- **Token:** Generate from User Settings → Access Tokens

### 3. Unity Catalog Setup

Ensure these resources exist (or will be created):

**Catalogs:**
- `retail_project` (prod)
- `retail_project_dev` (dev)
- `retail_project_test` (test)

**Schemas per catalog:**
- `postgress_bronze`
- `salesforce`
- `blob_storge`
- `retail_silver`
- `retail_gold`
- `retail_semantic`

**Volumes:**
- `retail_project.volume.blob_s`

## Deployment Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/omaga333/retail-data-platform-databricks.git
cd retail-data-platform-databricks
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi***

# Service Principals
SP_TEST=test-sp@company.com
SP_PROD=prod-sp@company.com

# Notification Email
NOTIFICATION_EMAIL=data-team@company.com

# Unity Catalog Connections
POSTGRES_CONNECTION=postgres_retail
SALESFORCE_CONNECTION=sales_retail
```

### Step 3: Create Unity Catalog Connections

**PostgreSQL Connection:**
```sql
CREATE CONNECTION postgres_retail
TYPE POSTGRES
OPTIONS (
  host 'postgres.example.com',
  port '5432',
  database 'retail_db',
  user 'dbuser',
  password secret('scope', 'postgres-password')
);
```

**Salesforce Connection (OAuth):**
```sql
CREATE CONNECTION sales_retail
TYPE SALESFORCE
OPTIONS (
  clientId secret('scope', 'sf-client-id'),
  clientSecret secret('scope', 'sf-client-secret'),
  authUrl 'https://login.salesforce.com',
  oauthType 'REFRESH_TOKEN',
  refreshToken secret('scope', 'sf-refresh-token')
);
```

### Step 4: Validate Bundle

```bash
databricks bundle validate -t dev
```

**Expected Output:**
```
✅ Configuration is valid
```

**Common Validation Errors:**
- Missing variables → Add to `.env` or `databricks.yml`
- Invalid resource references → Check pipeline IDs
- Permission errors → Verify workspace access

### Step 5: Deploy to Development

```bash
databricks bundle deploy -t dev
```

**What Happens:**
1. Bundle uploads source files to workspace
2. Creates/updates pipelines:
   - `[dev] PostgreSQL to Bronze`
   - `[dev] Salesforce to Bronze`
   - `[dev] Retail Transformation`
3. Creates/updates job:
   - `[dev] Retail Data Pipeline`
4. Sets permissions
5. Displays deployment summary

### Step 6: Run Initial Pipeline

```bash
databricks bundle run retail_job -t dev
```

Or trigger manually in UI:
1. Navigate to Workflows → Jobs
2. Find `[dev] Retail Data Pipeline`
3. Click "Run now"

### Step 7: Monitor Execution

**View Job Run:**
```bash
databricks jobs list-runs --job-id <job-id> --limit 1
```

**View Pipeline Status:**
```bash
databricks pipelines get <pipeline-id>
```

**UI Monitoring:**
1. Jobs → `[dev] Retail Data Pipeline` → Latest run
2. Pipelines → Monitor each pipeline individually
3. Check event logs for detailed execution traces

## Deployment to Test/Production

### Test Environment

**Pre-requisites:**
- Test catalog created: `retail_project_test`
- Test service principal configured: `test-sp@company.com`
- Service principal has appropriate permissions

**Deploy:**
```bash
databricks bundle deploy -t test
```

**Run:**
```bash
databricks bundle run retail_job -t test
```

### Production Environment

⚠️ **Production deployment requires additional approvals and validation.**

**Pre-requisites:**
1. All tests passed in `test` environment
2. Production service principal configured: `prod-sp@company.com`
3. Production catalog exists: `retail_project`
4. Change management approval obtained

**Deploy:**
```bash
databricks bundle deploy -t prod
```

**Verify Before Running:**
```bash
databricks bundle validate -t prod
databricks jobs get --job-id <prod-job-id>
```

**Run:**
```bash
databricks bundle run retail_job -t prod
```

**Post-Deployment:**
1. Monitor first run closely
2. Verify data quality expectations
3. Check dashboard refresh
4. Set up alerting

## Environment-Specific Configuration

### Development (`dev`)
- **Mode:** development
- **Run As:** Current user ({{workspace.current_user.userName}})
- **Catalog:** `retail_project_dev`
- **Purpose:** Local development and testing
- **Schedule:** Disabled (manual trigger only)

### Test (`test`)
- **Mode:** development
- **Run As:** Service principal ({{var.sp_test}})
- **Catalog:** `retail_project_test`
- **Purpose:** Integration testing and QA
- **Schedule:** Nightly at 2 AM

### Production (`prod`)
- **Mode:** production
- **Run As:** Service principal ({{var.sp_prod}})
- **Catalog:** `retail_project`
- **Purpose:** Production workloads
- **Schedule:** Daily at 2 AM
- **Permissions:** Restricted to data engineering team

## CI/CD Integration

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Databricks Bundle

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Databricks CLI
        run: pip install databricks-cli
      
      - name: Validate Bundle
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: databricks bundle validate -t dev
      
      - name: Deploy to Dev (on PR)
        if: github.event_name == 'pull_request'
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: databricks bundle deploy -t dev
      
      - name: Deploy to Prod (on merge to main)
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: databricks bundle deploy -t prod
```

**Required Secrets:**
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`

## Rollback Procedure

If a deployment fails or causes issues:

### 1. Identify Previous Working Version
```bash
git log --oneline
```

### 2. Checkout Previous Version
```bash
git checkout <previous-commit-hash>
```

### 3. Redeploy
```bash
databricks bundle deploy -t <target>
```

### 4. For Immediate Rollback (Production)
```bash
# Pause the job
databricks jobs update --job-id <job-id> --pause-status PAUSED

# Or delete and recreate from previous bundle version
databricks bundle destroy -t prod
git checkout <stable-version>
databricks bundle deploy -t prod
```

## Post-Deployment Checklist

- [ ] All pipelines show "IDLE" or "RUNNING" status
- [ ] First job run completed successfully
- [ ] All data quality expectations passed
- [ ] Unity Catalog tables created in correct schemas
- [ ] Dashboards are accessible and refreshing
- [ ] Alerting is configured
- [ ] Team has appropriate permissions
- [ ] Documentation is updated
- [ ] Monitoring dashboards are set up

## Troubleshooting Deployment Issues

See [Troubleshooting.md](Troubleshooting.md) for common deployment issues and solutions.

## Support

For deployment issues:
1. Check [Troubleshooting.md](Troubleshooting.md)
2. Review Databricks event logs
3. Contact: data-team@company.com
4. File an issue: https://github.com/omaga333/retail-data-platform-databricks/issues
