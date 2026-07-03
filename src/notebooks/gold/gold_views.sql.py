%sql
-- Databricks notebook source
CREATE OR REPLACE VIEW retail_project.retail_gold.dim_customer AS

SELECT
    id AS customer_id,
    customer_name,
    type AS customer_type,

    billing_city,
    billing_state,
    billing_country,
    phone,
    website,
    industry,
    number_of_employees,

    description

FROM retail_project.retail_silver.account

WHERE is_deleted = false and is_active=true;

-- COMMAND ----------

CREATE OR REPLACE VIEW retail_project.retail_gold.dim_product AS

SELECT
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    unit_price,
    supplier_name,
    launch_date,
    updated_at

FROM retail_project.retail_silver.product_catalog
where is_active=true;

-- COMMAND ----------

CREATE OR REPLACE VIEW retail_project.retail_gold.fact_inventory AS

SELECT
    inventory_id,
    product_id,
    stock_quantity,
    reorder_level,
    inventory_status,
    warehouse_location,
    last_stock_update
FROM retail_project.retail_silver.inventory;
