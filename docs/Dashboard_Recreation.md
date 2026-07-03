# Dashboard Recreation Guide

## Overview

Databricks Lakeview Dashboards cannot be directly exported as part of Asset Bundles yet. This guide documents how to recreate the **Executive Retail Analytics** dashboard manually after deploying the bundle.

## Dashboard: Executive Retail Analytics

**Original Dashboard ID:** `01f175cb286c1c8a9385a69c2c368319`  
**Location:** `/Users/aajahhs712@gmail.com/Executive Retail Analytics.lvdash.json`

### Data Source

The dashboard uses the **Semantic Layer** metric view:
```
retail_project.retail_semantic.retail_metrics
```

This view provides Genie-ready metrics with unified business definitions.

## Recreation Steps

### 1. Create New Lakeview Dashboard

1. Navigate to **Dashboards** in the Databricks workspace
2. Click **"Create Dashboard"**
3. Name it: `Executive Retail Analytics`
4. Select **Lakeview** as the dashboard type

### 2. Configure Data Source

1. Click **"Add Data Source"**
2. Select **SQL Warehouse** (or Serverless)
3. Choose the appropriate warehouse for your environment

### 3. Key Visualizations to Add

#### Visualization 1: Total Revenue (KPI Card)

**Query:**
```sql
SELECT SUM(amount) as total_revenue
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 30)
```

**Visualization Type:** Counter (KPI Card)
- **Format:** Currency (USD)
- **Decimal Places:** 2

#### Visualization 2: Revenue Trend (Line Chart)

**Query:**
```sql
SELECT
  transaction_date,
  SUM(amount) as daily_revenue
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY transaction_date
ORDER BY transaction_date
```

**Visualization Type:** Line Chart
- **X-axis:** `transaction_date`
- **Y-axis:** `daily_revenue`
- **Format Y-axis:** Currency
- **Title:** "Revenue Trend (Last 90 Days)"

#### Visualization 3: Top Products by Revenue (Bar Chart)

**Query:**
```sql
SELECT
  product_name,
  SUM(amount) as product_revenue
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY product_name
ORDER BY product_revenue DESC
LIMIT 10
```

**Visualization Type:** Horizontal Bar Chart
- **X-axis:** `product_revenue`
- **Y-axis:** `product_name`
- **Title:** "Top 10 Products by Revenue (Last 30 Days)"

#### Visualization 4: Revenue by Category (Pie Chart)

**Query:**
```sql
SELECT
  category,
  SUM(amount) as category_revenue
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY category
ORDER BY category_revenue DESC
```

**Visualization Type:** Pie Chart
- **Label:** `category`
- **Value:** `category_revenue`
- **Title:** "Revenue Distribution by Category"

#### Visualization 5: Sales by Channel (Stacked Bar Chart)

**Query:**
```sql
SELECT
  sales_channel,
  category,
  SUM(amount) as channel_category_revenue
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY sales_channel, category
ORDER BY sales_channel, channel_category_revenue DESC
```

**Visualization Type:** Stacked Bar Chart
- **X-axis:** `sales_channel`
- **Y-axis:** `channel_category_revenue`
- **Color:** `category`
- **Title:** "Revenue by Sales Channel and Category"

#### Visualization 6: Customer Metrics (Table)

**Query:**
```sql
SELECT
  customer_name,
  COUNT(DISTINCT transaction_id) as transaction_count,
  SUM(amount) as total_spent,
  AVG(amount) as avg_transaction_value
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY customer_name
ORDER BY total_spent DESC
LIMIT 20
```

**Visualization Type:** Table
- **Columns:** All
- **Format:**
  - `total_spent`: Currency (USD)
  - `avg_transaction_value`: Currency (USD)
  - `transaction_count`: Number
- **Title:** "Top 20 Customers by Spend"

#### Visualization 7: Geographic Distribution (Map)

**Query:**
```sql
SELECT
  billing_country,
  billing_state,
  billing_city,
  SUM(amount) as location_revenue
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND billing_country IS NOT NULL
GROUP BY billing_country, billing_state, billing_city
ORDER BY location_revenue DESC
LIMIT 100
```

**Visualization Type:** Map (if supported) or Table
- **Location Columns:** `billing_country`, `billing_state`, `billing_city`
- **Value:** `location_revenue`
- **Title:** "Revenue by Location"

#### Visualization 8: Monthly Revenue Comparison (Bar Chart)

**Query:**
```sql
SELECT
  year,
  month_name,
  SUM(amount) as monthly_revenue
FROM retail_project.retail_semantic.retail_metrics
WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY year, month_name, month
ORDER BY year, month
```

**Visualization Type:** Bar Chart
- **X-axis:** `month_name`
- **Y-axis:** `monthly_revenue`
- **Color:** `year` (for year-over-year comparison)
- **Title:** "Monthly Revenue (Year-over-Year)"

### 4. Add Filters

Add dashboard-level filters for interactivity:

1. **Date Range Filter:**
   ```sql
   SELECT DISTINCT transaction_date
   FROM retail_project.retail_semantic.retail_metrics
   ORDER BY transaction_date DESC
   ```
   - **Filter Type:** Date Range
   - **Default:** Last 30 days

2. **Category Filter:**
   ```sql
   SELECT DISTINCT category
   FROM retail_project.retail_semantic.retail_metrics
   WHERE category IS NOT NULL
   ORDER BY category
   ```
   - **Filter Type:** Multi-select dropdown
   - **Default:** All categories

3. **Sales Channel Filter:**
   ```sql
   SELECT DISTINCT sales_channel
   FROM retail_project.retail_semantic.retail_metrics
   WHERE sales_channel IS NOT NULL
   ORDER BY sales_channel
   ```
   - **Filter Type:** Multi-select dropdown
   - **Default:** All channels

### 5. Dashboard Layout

Arrange visualizations in a 2-column grid:

```
+-------------------------+-------------------------+
|    Total Revenue KPI    |   Transaction Count KPI |
+-------------------------+-------------------------+
|         Revenue Trend (full width)                |
+---------------------------------------------------+
| Top Products (left)     | Revenue by Category (R) |
+-------------------------+-------------------------+
|    Sales by Channel (full width)                  |
+---------------------------------------------------+
|         Customer Metrics Table (full width)       |
+---------------------------------------------------+
|      Geographic Distribution (full width)         |
+---------------------------------------------------+
|   Monthly Revenue Comparison (full width)         |
+---------------------------------------------------+
```

### 6. Configure Refresh Schedule

1. Click **"Schedule"** in dashboard settings
2. Set refresh frequency: **Daily at 3 AM** (after pipeline runs)
3. Configure email subscriptions for stakeholders

### 7. Set Permissions

```sql
-- Grant view access to data analysts
GRANT SELECT ON VIEW retail_project.retail_semantic.retail_metrics
TO `data-analysts@company.com`;

-- Dashboard permissions (UI-based)
-- Add viewers: data-analysts, business-users
-- Add editors: data-engineering-team
```

### 8. Export Dashboard Definition (Optional)

For backup purposes, export the dashboard as JSON:

1. Open the dashboard
2. Click **"···"** (more options)
3. Select **"Export as JSON"**
4. Save to: `resources/dashboards/executive_retail_analytics.json`

## Alternative: Genie Space

Instead of manually recreating the dashboard, consider creating a **Genie Space** powered by the semantic layer:

### Create Genie Space

1. Navigate to **Genie** in Databricks
2. Click **"Create Space"**
3. Name: `Retail Analytics`
4. Add data source: `retail_project.retail_semantic.retail_metrics`
5. The semantic layer YAML definitions enable natural language queries

### Example Genie Queries

Users can ask:
- "What is total revenue last month?"
- "Show me top 10 products by sales"
- "Compare revenue by category year over year"
- "Which customers spent the most last quarter?"
- "Revenue trend by sales channel"

Genie uses the metric definitions, dimensions, and synonyms from the semantic layer to understand these queries.

## Future Enhancement

**Automated Dashboard Creation:**
Once Databricks supports Lakeview Dashboards in Asset Bundles, this manual process can be replaced with:

```yaml
resources:
  dashboards:
    executive_retail_analytics:
      name: "[${bundle.target}] Executive Retail Analytics"
      definition_path: ./resources/dashboards/executive_retail_analytics.json
      permissions:
        - level: CAN_VIEW
          group_name: data_analysts
```

## Support

For help recreating dashboards:
- **Documentation:** This guide
- **Contact:** data-team@company.com
- **Semantic Layer:** See `/src/notebooks/semantic/retail_metrics.sql`
