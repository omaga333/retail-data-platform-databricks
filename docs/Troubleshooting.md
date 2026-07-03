# Troubleshooting Guide - Retail Data Platform

Common issues and their solutions for the Retail Data Platform Databricks Asset Bundle.

## Salesforce Connection Issues

### Issue: OAuth Token Exchange Failed

**Error Message:**
```
SAAS_CONNECTOR_UC_CONNECTION_OAUTH_EXCHANGE_FAILED
The OAuth token exchange failed for UC connection: sales_retail.
```

**Root Cause:**
- OAuth refresh token has expired
- Connected App credentials are invalid
- User who authenticated has lost access or changed password

**Solution:**

1. **Navigate to Unity Catalog Connections:**
   ```
   Catalog → Connections → sales_retail
   ```

2. **Re-authenticate the connection:**
   - Click "Edit connection"
   - Click "Authenticate" button
   - Log in to Salesforce with appropriate credentials
   - Authorize the Databricks connected app
   - Save the connection

3. **Verify connection:**
   ```bash
   # Use the Salesforce validation tool (if available)
   # Or test by running the pipeline
   databricks pipelines start-update --pipeline-id <salesforce-pipeline-id>
   ```

4. **Alternative - Create new connection:**
   ```sql
   CREATE CONNECTION sales_retail_new
   TYPE SALESFORCE
   OPTIONS (
     clientId secret('scope', 'sf-client-id'),
     clientSecret secret('scope', 'sf-client-secret'),
     authUrl 'https://login.salesforce.com',
     oauthType 'REFRESH_TOKEN',
     refreshToken secret('scope', 'sf-refresh-token-new')
   );
   ```

**Prevention:**
- Set up automated monitoring for connection health
- Document OAuth refresh token expiration policy
- Use a service account for Salesforce authentication

### Issue: Salesforce Object Access Denied

**Error Message:**
```
HTTP 403: Forbidden - Access denied to Salesforce object: Account
```

**Solution:**
1. Verify the Salesforce user has "Read" permission on Account and Opportunity objects
2. Check Salesforce Profile and Permission Sets
3. Ensure the user has "API Enabled" permission

## Pipeline Failures

### Issue: Pipeline Stuck in INITIALIZING

**Symptoms:**
- Pipeline shows "INITIALIZING" for > 5 minutes
- No event logs generated

**Common Causes:**
1. Serverless compute not available in region
2. Connection authentication failure
3. Unity Catalog permissions issue

**Solution:**
```bash
# 1. Check pipeline status
databricks pipelines get --pipeline-id <pipeline-id>

# 2. Cancel stuck update
databricks pipelines stop --pipeline-id <pipeline-id>

# 3. Review pipeline configuration
databricks pipelines get --pipeline-id <pipeline-id> | jq '.spec'

# 4. Restart with full refresh
databricks pipelines start-update --pipeline-id <pipeline-id> --full-refresh
```

### Issue: Data Quality Expectation Failures

**Error Message:**
```
Expectation 'valid_product_id' failed for 150 records
```

**Solution:**

1. **Review failed records:**
   ```sql
   SELECT * FROM retail_project.retail_silver.product_catalog
   WHERE product_id IS NULL OR TRIM(product_id) = ''
   LIMIT 100;
   ```

2. **Options:**
   - Fix data at source
   - Adjust expectation (if business rule changed)
   - Use `expect_or_drop` instead of `expect` to drop invalid records

3. **Temporarily bypass (dev only):**
   ```python
   @dp.table(name="...")
   # @dp.expect_or_drop("valid_product_id", "product_id IS NOT NULL")  # Commented out
   def product_catalog_silver():
       ...
   ```

## Job Failures

### Issue: Task Dependency Failure

**Error Message:**
```
Task 'salesforce_to_bronze' failed, skipping downstream task 'silver_and_gold'
```

**Solution:**

1. **Check task run_if condition:**
   ```yaml
   - task_key: blob_to_bronze
     run_if: AT_LEAST_ONE_FAILED  # Only runs if previous task failed
   ```

2. **Review job configuration:**
   - Check `depends_on` relationships
   - Verify `run_if` conditions make sense
   - Ensure no circular dependencies

3. **Manual task retry:**
   ```bash
   databricks jobs run-now --job-id <job-id>
   ```

### Issue: Notebook Task Fails

**Error Message:**
```
Notebook execution failed: No such file or directory
```

**Solution:**
1. **Verify notebook path:**
   ```yaml
   notebook_task:
     notebook_path: ${workspace.file_path}/src/notebooks/bronze/blob_to_bronze
     source: WORKSPACE
   ```

2. **Check notebook exists:**
   - Navigate to workspace
   - Verify path: `/Repos/<user>/retail-data-platform-databricks/src/notebooks/bronze/blob_to_bronze`

3. **Redeploy bundle:**
   ```bash
   databricks bundle deploy -t dev --force
   ```

## Unity Catalog Issues

### Issue: Schema Not Found

**Error Message:**
```
Schema 'retail_project.retail_silver' not found
```

**Solution:**

1. **Create missing schema:**
   ```sql
   CREATE SCHEMA IF NOT EXISTS retail_project.retail_silver
   COMMENT 'Silver layer - curated data';
   ```

2. **Verify catalog exists:**
   ```sql
   SHOW CATALOGS LIKE 'retail_project%';
   ```

3. **Check permissions:**
   ```sql
   SHOW GRANTS ON CATALOG retail_project;
   ```

### Issue: Permission Denied

**Error Message:**
```
User does not have permission to CREATE TABLE in schema retail_project.retail_silver
```

**Solution:**

1. **Grant required permissions:**
   ```sql
   GRANT USE CATALOG ON CATALOG retail_project TO `user@company.com`;
   GRANT USE SCHEMA ON SCHEMA retail_project.retail_silver TO `user@company.com`;
   GRANT CREATE TABLE ON SCHEMA retail_project.retail_silver TO `user@company.com`;
   GRANT MODIFY ON SCHEMA retail_project.retail_silver TO `user@company.com`;
   GRANT SELECT ON SCHEMA retail_project.retail_silver TO `user@company.com`;
   ```

2. **For service principals:**
   ```sql
   GRANT USE CATALOG ON CATALOG retail_project TO `prod-sp@company.com`;
   GRANT ALL PRIVILEGES ON SCHEMA retail_project.* TO `prod-sp@company.com`;
   ```

## Bundle Deployment Issues

### Issue: Validation Errors

**Error Message:**
```
Error: variable 'catalog' is not defined
```

**Solution:**
1. **Add missing variables to `.env`:**
   ```env
   CATALOG=retail_project
   ```

2. **Or define in `databricks.yml`:**
   ```yaml
   variables:
     catalog:
       default: retail_project
   ```

### Issue: Resource Already Exists

**Error Message:**
```
Error: job with name '[dev] Retail Data Pipeline' already exists
```

**Solution:**
```bash
# Option 1: Use --force to update
databricks bundle deploy -t dev --force

# Option 2: Destroy and recreate
databricks bundle destroy -t dev
databricks bundle deploy -t dev
```

## Performance Issues

### Issue: Slow Pipeline Execution

**Symptoms:**
- Pipeline takes > 1 hour to complete
- Serverless compute not scaling

**Solution:**

1. **Enable Photon:**
   ```yaml
   pipelines:
     retail_transformation:
       photon: true
   ```

2. **Check for large shuffles:**
   - Review Spark UI
   - Look for skewed partitions
   - Consider repartitioning

3. **Optimize Delta tables:**
   ```sql
   OPTIMIZE retail_project.retail_silver.product_catalog
   ZORDER BY (category, subcategory);
   ```

### Issue: Out of Memory Errors

**Error Message:**
```
java.lang.OutOfMemoryError: GC overhead limit exceeded
```

**Solution:**
1. Use serverless compute (auto-scales)
2. Reduce data volume per batch
3. Increase checkpoint interval
4. Partition large tables by date

## Network Connectivity Issues

### Issue: Cannot Connect to PostgreSQL

**Error Message:**
```
Connection refused: postgres.example.com:5432
```

**Solution:**
1. **Verify network connectivity:**
   - Check firewall rules
   - Verify IP allowlist includes Databricks serverless IPs
   - Test from Databricks notebook

2. **Check connection settings:**
   ```sql
   DESCRIBE CONNECTION postgres_retail;
   ```

3. **Use private endpoint (if available):**
   - Configure VPC peering
   - Use PrivateLink (AWS) or Private Link (Azure)

## Data Issues

### Issue: Missing Data in Silver Layer

**Symptoms:**
- Bronze tables have data
- Silver tables are empty or incomplete

**Solution:**

1. **Check data quality expectations:**
   ```sql
   SELECT COUNT(*) as bronze_count FROM retail_project.postgress_bronze.product_catalog;
   SELECT COUNT(*) as silver_count FROM retail_project.retail_silver.product_catalog;
   ```

2. **Review event logs:**
   - Look for `expect_or_drop` violations
   - Check for processing errors

3. **Run full refresh:**
   ```bash
   databricks pipelines start-update --pipeline-id <pipeline-id> --full-refresh
   ```

### Issue: Duplicate Records

**Symptoms:**
- Primary key violations
- Duplicate rows in tables

**Solution:**

1. **Check SCD Type 2 configuration:**
   - Verify `__IS_CURRENT` flag
   - Filter on `__END_AT IS NULL`

2. **Deduplicate manually:**
   ```sql
   CREATE OR REPLACE TABLE retail_project.retail_silver.account_dedup AS
   SELECT * FROM retail_project.retail_silver.account
   WHERE __END_AT IS NULL;
   ```

## Getting Help

### 1. Check Documentation
- [Architecture.md](Architecture.md)
- [Deployment.md](Deployment.md)
- [Databricks Documentation](https://docs.databricks.com)

### 2. Review Logs
```bash
# Job run logs
databricks jobs runs get-output --run-id <run-id>

# Pipeline event logs
# Access via UI: Pipelines → <pipeline-name> → Event logs
```

### 3. Contact Support
- **Email:** data-team@company.com
- **GitHub Issues:** https://github.com/omaga333/retail-data-platform-databricks/issues
- **Databricks Support:** https://help.databricks.com

### 4. Diagnostic Commands

```bash
# Bundle status
databricks bundle validate -t <target>

# List all resources
databricks jobs list
databricks pipelines list

# Check workspace files
databricks workspace ls /Repos/<user>/retail-data-platform-databricks

# View Unity Catalog
databricks unity-catalog catalogs list
databricks unity-catalog schemas list --catalog-name retail_project
```
