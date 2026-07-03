# Retail Data Platform - Architecture Documentation

## Overview

The Retail Data Platform implements a modern **Medallion Architecture** on Databricks, providing a scalable, maintainable, and production-ready data platform for retail analytics.

## Architecture Layers

### 1. Bronze Layer (Raw Data)

**Purpose:** Store raw, unprocessed data exactly as received from source systems.

#### Data Sources

**A. PostgreSQL Database**
- **Pipeline:** `postgres_ingestion`
- **Connection:** `postgres_retail`
- **Type:** Managed Ingestion (CDC or Query-based)
- **Destination:** `retail_project.postgress_bronze`
- **Tables:**
  - `product_catalog` - Product master data
  - `inventory` - Inventory levels and warehouse info
  - Additional tables as configured

**B. Salesforce**
- **Pipeline:** `salesforce_ingestion`
- **Connection:** `sales_retail` (OAuth)
- **Type:** Managed Ingestion with SCD Type 2
- **Destination:** `retail_project.salesforce`
- **Objects:**
  - `Account` - Customer master (SCD Type 2 enabled)
  - `Opportunity` - Sales opportunities
  - Includes `__START_AT`, `__END_AT`, `__IS_CURRENT` columns for change tracking

**C. Azure Blob Storage**
- **Pipeline:** `blob_to_bronze` notebook
- **Type:** Auto Loader (Structured Streaming)
- **Destination:** `retail_project.blob_storge.transactions`
- **Format:** CSV files
- **Features:**
  - Schema inference and evolution
  - Checkpoint-based exactly-once semantics

### 2. Silver Layer (Curated Data)

**Purpose:** Cleaned, standardized, and validated data ready for business use.

**Pipeline:** `retail_transformation` (Lakeflow Spark Declarative Pipeline)

#### Transformations

**A. Product Catalog** (`product_catalog.py`)
- **Source:** `postgress_bronze.product_catalog`
- **Destination:** `retail_silver.product_catalog`
- **Transformations:**
  - Trim and clean string fields
  - Uppercase standardization for categories
  - Null handling for optional fields
  - Add processing timestamp
- **Data Quality:**
  - `expect_or_drop`: Valid product_id, product_name, unit_price >= 0
  - `expect`: Valid launch_date and updated_at

**B. Inventory** (`inventory.py`)
- **Source:** `postgress_bronze.inventory`
- **Destination:** `retail_silver.inventory`
- **Transformations:**
  - Calculate `inventory_status` (LOW_STOCK vs HEALTHY)
  - Standardize column names
- **Data Quality:**
  - `expect_or_drop`: Non-null inventory_id
  - `expect`: Valid stock_quantity > 0, non-null product_id and store_id

**C. Account** (`account.py`)
- **Source:** `salesforce.account`
- **Destination:** `retail_silver.account`
- **Transformations:**
  - Uppercase and trim customer names
  - Coalesce industry with "UNKNOWN" default
  - Compute `is_active` from `__END_AT` (SCD Type 2 active record indicator)
  - Standardize column naming (snake_case)
- **Data Quality:**
  - `expect_or_drop`: Non-null id
  - `expect`: Non-null customer_name

**D. Opportunity** (`opportunity.py`)
- **Source:** `salesforce.opportunity`
- **Destination:** `retail_silver.opportunity`
- **Transformations:**
  - Calculate `deal_size` category (ENTERPRISE/MID_MARKET/SMALL)
  - Standardize column naming
- **Data Quality:**
  - `expect_or_drop`: Non-null id and name
  - `expect`: Valid amount >= 0, probability 0-100%, valid stage_name

### 3. Gold Layer (Business-Ready Views)

**Purpose:** Aggregated, denormalized data optimized for analytics and reporting.

#### Business Views

**A. Dimension: Customer** (`dim_customer`)
```sql
SELECT
    id AS customer_id,
    customer_name,
    type AS customer_type,
    billing_city, billing_state, billing_country,
    phone, website, industry, number_of_employees,
    description
FROM retail_silver.account
WHERE is_deleted = false AND is_active = true
```

**B. Dimension: Product** (`dim_product`)
```sql
SELECT
    product_id, product_name, category, subcategory,
    brand, unit_price, supplier_name,
    launch_date, updated_at
FROM retail_silver.product_catalog
WHERE is_active = true
```

**C. Fact: Inventory** (`fact_inventory`)
```sql
SELECT
    inventory_id, product_id,
    stock_quantity, reorder_level, inventory_status,
    warehouse_location, last_stock_update
FROM retail_silver.inventory
```

**D. Calendar Dimension** (`calendar`)
- Date spine for time-series analysis
- Includes: year, quarter, month, week, day attributes
- Weekend/weekday flags
- Parameterized with `:start_date` and `:end_date`

### 4. Semantic Layer (Metrics & BI)

**Purpose:** Genie-ready unified metric definitions for conversational analytics.

**View:** `retail_metrics` (Databricks Semantic Layer with YAML)

#### Structure

**Source:** `retail_gold.fact_sales`

**Joins:**
- `product` → `retail_gold.dim_product`
- `calendar` → `retail_gold.calendar`
- `customer` → `retail_gold.dim_customer`

**Dimensions:**
- Transaction Date, Year, Quarter, Month
- Product Category, Brand
- Payment Mode, Sales Channel
- Customer Type, Name, Location (City, State, Country)
- Industry

**Measures:**
- Transaction Count
- Total Revenue (currency, USD)
- Total Quantity Sold
- Total Discount
- Average Transaction Value
- Unique Customers

**Format:** YAML-based metric definitions with synonyms for natural language queries

## Data Flow

```
PostgreSQL ──┐
              ├──> Bronze Layer ──> Silver Layer ──> Gold Layer ──> Semantic Layer
Salesforce ──┤                                                           │
              │                                                           v
Blob Storage ─┘                                                    Genie Space
                                                                   Dashboards
```

## Orchestration

**Job:** `retail_job`

**Task Dependencies:**
1. `postgres_to_bronze` - Run PostgreSQL ingestion
2. `salesforce_to_bronze` - Run Salesforce ingestion (depends on #1)
3. `blob_to_bronze` - Run blob ingestion (depends on #2, run_if: AT_LEAST_ONE_FAILED)
4. `silver_and_gold` - Run transformation pipeline (depends on #3)
5. `dashboard` - Refresh dashboard (depends on #4)

**Schedule:** Daily at 2 AM (quartz cron: `0 0 2 * * ?`)

## Unity Catalog Structure

```
retail_project (catalog)
├── postgress_bronze (schema) - PostgreSQL raw data
│   ├── product_catalog
│   └── inventory
│
├── salesforce (schema) - Salesforce raw data
│   ├── account (SCD Type 2)
│   └── opportunity
│
├── blob_storge (schema) - Blob storage raw data
│   └── transactions
│
├── retail_silver (schema) - Curated data
│   ├── product_catalog
│   ├── inventory
│   ├── account
│   └── opportunity
│
├── retail_gold (schema) - Business views
│   ├── dim_customer (view)
│   ├── dim_product (view)
│   ├── fact_inventory (view)
│   └── calendar (table)
│
└── retail_semantic (schema) - Metrics layer
    └── retail_metrics (view with YAML metrics)
```

## Security & Governance

### Unity Catalog Connections

1. **postgres_retail**
   - Type: PostgreSQL
   - Authentication: Username/password or IAM
   - Network: Private endpoint or IP allowlist

2. **sales_retail**
   - Type: Salesforce
   - Authentication: OAuth 2.0 (requires periodic re-auth)
   - Permissions: Read access to Account and Opportunity objects

### Access Control

**Data Engineering Team:**
- `USE CATALOG` on `retail_project`
- `CREATE SCHEMA`, `CREATE TABLE`, `MODIFY`, `SELECT` on all schemas

**Data Analysts:**
- `USE CATALOG` on `retail_project`
- `USE SCHEMA`, `SELECT` on `retail_gold` and `retail_semantic`

**Service Principals:**
- `test-sp`: Deploy and run in test environment
- `prod-sp`: Deploy and run in production environment

## Performance Optimizations

1. **Auto Optimize**
   - `optimizeWrite`: Enabled on all tables
   - `autoCompact`: Enabled on all tables

2. **Clustering**
   - `product_catalog`: Clustered by `[category, subcategory]`

3. **Serverless Compute**
   - All pipelines use serverless for auto-scaling

4. **Photon Engine**
   - Enabled on transformation pipeline for faster query execution

## Monitoring & Observability

**Event Logs:** Available in pipeline monitoring UI
- Per-table metrics (`flow_progress`)
- Processing latency
- Data quality expectations results

**Job Notifications:**
- Email alerts on failure
- Configurable via `notification_email` variable

## Disaster Recovery

**Data Retention:**
- Bronze: Indefinite (source of truth)
- Silver: 30 days time travel
- Gold: 7 days time travel

**Backup Strategy:**
- Unity Catalog managed tables
- Delta Lake time travel
- Incremental backups via Delta `OPTIMIZE` and `VACUUM`

## Scalability Considerations

1. **Horizontal Scaling:** Serverless compute auto-scales based on workload
2. **Data Partitioning:** Partition large fact tables by date
3. **Incremental Processing:** Use streaming for continuous ingestion
4. **SCD Type 2:** Efficient change tracking without full reloads

## Future Enhancements

- [ ] Add machine learning feature store
- [ ] Implement data quality dashboard
- [ ] Add real-time streaming from Kafka/EventHub
- [ ] Implement GDPR compliance (PII masking)
- [ ] Add CI/CD pipeline with GitHub Actions
