# Building a Smart Retail Data Platform Using Medallion Architecture on Databricks


# Section One: Comprehensive Sequential Project Documentation

Below is the comprehensive, sequential documentation of the project. All sections have been merged in a logical order that illustrates the architecture, the data ingestion strategy, transformation processes, and best practices, making it ready for use as a professional reference or as part of your portfolio.

## 1. Project Overview (Executive Summary)

This project aims to build a comprehensive, automated, and scalable data pipeline using the **Databricks** platform. The project relies on the **Medallion Architecture (Bronze, Silver, Gold)** to ingest data from multiple, diverse sources (databases, CRM systems, and cloud files), then clean it, standardize it, and apply Data Quality rules to it, so that it becomes ready for advanced analytics and insight extraction in the Gold layer.

---

## 2. Infrastructure and Technologies (Architecture & Tech Stack)

The latest technologies in the cloud environment were adopted to ensure efficiency and scalability:

* **Core Platform:** Databricks.
* **Governance & Access Management:** Unity Catalog.
* **Processing Engine:** Apache Spark (PySpark).
* **Transformation Framework:** LakeFlow Spark Declarative Pipelines / Delta Live Tables (DLT).
* **Data Ingestion Tools:** Databricks LakeFlow Connect & Auto Loader (`cloudFiles`).

---

## 3. Data Ingestion Strategy and the Bronze Layer (Data Ingestion & Bronze Layer)

The **Bronze** layer represents the raw data exactly as it comes from the source, while retaining the history of modifications to ensure no data is lost. To ensure efficient data transfer, a **Hybrid Ingestion Strategy** was adopted, relying on two main tools depending on the nature of the source:

### A. Ingestion via LakeFlow Connect (for structured sources)

**LakeFlow Connect** was used as the primary connection tool to pull data from databases and CRM systems, given its support for Native Connectors and its ability to automatically capture incremental changes (CDC).

* **Database Management System (PostgreSQL):** `product_catalog`, `inventory` tables.
* **Customer Relationship Management System (Salesforce):** `account`, `opportunity` tables (containing data in `PascalCase` format and many unused columns).

### B. Ingestion via Auto Loader (for unstructured files)

Since LakeFlow Connect is not designed to handle open folders and files, the **Auto Loader** engine was used to ingest cloud files.

* **Source:** Cloud Storage (Blob Storage) - `transactions` table (CSV files).
* **Mechanism:** A Managed Volume was set up inside Unity Catalog to link the files. Auto Loader monitors the file path and reads new data incrementally (Incremental Load) using `Checkpoints`.
* **Flexibility:** `Schema Location` was used to detect any future changes in file structure, and the `_rescued_data` feature was enabled to isolate corrupted records without stopping the system.

---

## 4. The Cleansed Data Layer and Transformation Processes (Silver Layer Transformations)

The **Silver** layer represents the "unified and trusted version" of the data. This layer was built entirely using **LakeFlow Spark Declarative Pipelines (DLT)**.

LakeFlow automates infrastructure management, automatically manages Dependencies between tables, and applies built-in data quality rules. The following operations were implemented:

### Table-by-Table Specifications:

#### 4.1. Product Catalog Table (`product_catalog`)

* **Data Quality (DQ) Rules:** Product number and name must not be Null (`expect_or_drop`). Price must be > 0 (`expect`).
* **Transformations:**
* Text cleaning (`trim`, `initcap`).
* Filling empty values in `category`, `subcategory`, `brand` with `'Unknown'`.
* Rounding the price to two decimal places (`round`).
* Deriving the `is_active` column for active records based on `end_date` (applying SCD Type 2 logic).

#### 4.2. Inventory Table (`inventory`)

* **Data Quality (DQ) Rules:** Stock must be positive. Identifiers (`store_id`, `product_id`) must be present.
* **Transformations (Business Logic):**
* Adding a derived column `inventory_status`: if the quantity (`stock_quantity`) is less than the reorder level (`reorder_level`), it is marked as `"Low Stock"`, otherwise `"Healthy Stock"`.

#### 4.3. Account Table (`account`)

* **Transformations:**
* **Column Pruning:** Excluding unused default columns coming from Salesforce to reduce table size and speed up queries.
* Standardizing column names from `PascalCase` to `snake_case` (such as converting `Name` to `customer_name`).
* Deriving the `is_active` column to handle historical changes.

#### 4.4. Opportunity Table (`opportunity`)

* **Data Quality (DQ) Rules:** `probability` between 0 and 100. `stage` must be within a predefined list.
* **Transformations (Business Logic):**
* Adding a `deal_size` column to classify deals into: `"Enterprise"`, `"Mid-market"`, `"Small"` based on the deal value (`amount`).

#### 4.5. Transactions Table (`transactions`)

* **Data Quality (DQ) Rules:** `transaction_id` and `product_id` must not be Null. Quantity and price must be positive values. `payment_mode` must be within allowed values.
* **Transformations:**
* **Type Casting:** Converting quantity and price columns from `String` to `Integer`.
* **Timestamp Handling:** Converting the `transaction_timestamp` column from a complex string into a real `Timestamp` via `to_timestamp`.
* Adding a calculated column `gross_amount` (quantity × price).


## 5. Applied Engineering Best Practices

1. **Automatic Incremental Loading:** By using `readStream` with DLT and Auto Loader, the system processes only new data with high efficiency, saving compute cost and resources.
2. **Declarative Programming:** Focusing on describing the desired shape of the data, and leaving infrastructure complexities and task scheduling to the LakeFlow engine.
3. **Fault Tolerance:** The system does not collapse when faced with faulty data; instead, it drops it (Drop), allows it through with a warning (Expect), or isolates it in the rescue column (`_rescued_data`).
4. **Schema Evolution:** The system is able to accommodate any new columns added to the files in the future thanks to enabling schema merging features.
5. **Pruning & Clustering:** Dropping unnecessary columns and using `cluster_by` to physically organize the data and speed up queries for the Gold layer.

---

# Section Two: Comprehensive Technical Design Document

This is a comprehensive Technical Documentation, professionally designed to be ready for use in your portfolio or as a `README.md` file on GitHub. The document reflects your skills as a Junior AI Data Engineer in Cairo focused on building integrated data platforms using Python and PySpark, and applying deep DataOps concepts to understand "the machine from the inside" rather than just writing surface-level code.

## 📌 1. Project Overview

This project was designed to build an integrated End-to-End Cloud Data Platform based on the Medallion Architecture within the **Databricks** environment. The project aims to integrate sales and transaction data from multiple sources, clean it, model it, and make it ready for natural language queries using AI technologies (Databricks Genie AI).

* **Core Tech Stack:** Python, PySpark, Delta Lake, Databricks Pipelines (DLT), Databricks SQL, Databricks Genie, YAML.
* **Modeling Approach (Data Modeling):** Star Schema.
* **Orchestration:** Databricks Jobs.

---

## 🏗️ 2. Data Architecture (Medallion Architecture)

The data flow was divided into three main layers to ensure data quality and progression:

### A. Extraction Layer (Bronze Layer - Raw Data)

* **Goal:** Receiving raw data from sources exactly as it is, without modification.
* **Sources and Ingestion Mechanisms:**
1. **Postgres Database:** Pulled using a ready-made Pipeline (LakeFlow Connect).
2. **Salesforce System (Accounts and Opportunities data):** Pulled as streaming data.
3. **CSV Files (Transactions data):** Stored in Blob Storage and pulled using **Auto Loader** technology to handle Incremental Data.

### B. Cleansing and Standardization Layer (Silver Layer - Cleansed Data)

* **Goal:** Applying Data Quality standards and cleaning text.
* **Tools:** Using the `pyspark.pipelines` library (DLT).
* **Key Code Transformations:**
* **Text Cleaning:** Using `F.trim` and `F.upper` functions to standardize text.
* **Null Handling:** Converting empty strings `""` into `None` (NULL) using `F.when`.
* **Data Quality Rules (Expectations):**
* `@dp.expect_or_drop`: To delete completely invalid records (such as a missing product ID `id IS NOT NULL`).
* `@dp.expect`: To allow the record to pass through while logging an alert in the quality system (such as validating the launch date).
* **Feature Engineering:** Creating new columns such as `deal_size` to classify deal sizes into (ENTERPRISE, MID_MARKET, SMALL) based on sales values.

### C. Business and Reporting Layer (Gold Layer - Star Schema)

* **Goal:** Modeling the data to be ready for BI Tools with the fastest possible performance using the **Star Schema**.
* **Engineering Design of the Layer:**
1. **`fact_sales` Fact Table (Physical Table):**
* Built by merging (LEFT JOIN) the `transactions` table with the `opportunity` table using the `opportunity_name` key.
* Stored as a physical table due to it containing complex calculations and merges.
2. **`dim_customer` and `dim_product` Dimension Tables (Views):**
* Designed as Views using SQL to save storage space (Storage Optimization), since the data is already unified in the Silver layer.
* Filters for active records `WHERE is_deleted = false AND is_active = true` were applied to handle Slowly Changing Dimensions (SCD Type 2).
3. **`dim_calendar` Calendar Table (GenAI Generated):**
* Fully generated using **Databricks Genie**.
* Contains advanced SQL functions such as `explode(sequence(...))` to create a time sequence, and extracting complex business details (such as `is_weekend` and `is_last_day_of_month`).

---

## 🧠 3. Semantic Layer & Metric Views

* **Goal:** Building a "Single Source of Truth" to unify concepts and calculation formulas and prepare the platform for AI.
* **Implementation:** Using the **Metric Views** feature, written in **YAML** combined with SQL.
* **Components of the Metric View (`retail_metrics`):**
* **Source:** The `fact_sales` table.
* **Joins:** Predefined definitions linking the fact table to the dimension tables (products, customers, calendar).
* **Measures:** Definitions of calculation formulas such as total revenue `SUM(amount)`, and the count of distinct customers `COUNT(DISTINCT customer_id)`. Formats were configured to display them as currency (USD) or as integers.
* **Dimensions:** Defining descriptive columns while adding a **Synonyms** feature (such as linking the term `sale date` to `Transaction Date`) to make it easier for the AI engine to understand managers' questions.

---

## 📊 4. Consumption Layer

User interfaces suited to every management level were designed:

1. **Lakeview Dashboards:**
* Read data directly from the Semantic Layer to automatically inherit all formats and formulas.
* Include an (Executive Overview) with Key Performance Indicators (KPIs), sales trends over time, and product performance analysis.
2. **Genie Spaces:**
* A Conversational UI that allows managers to ask questions in plain English (such as: *"Which customer is doing max transactions?"*).
* Genie translates the question into complex SQL, executes it against the Gold tables, and returns the answer along with an illustrative chart. Settings (Instructions & Benchmark queries) were configured to ensure the accuracy of responses and their validity for a production environment (Production-ready).

---

## ⚙️ 5. Orchestration & DataOps

All the previous parts were connected to work as a synchronized automated system using **Databricks Jobs**.

* **Workflow Name:** `retail Q end to end job`
* **Task Sequence (DAG Dependencies):**
1. Fetching Postgres data.
2. Fetching Salesforce data.
3. Fetching Blob Storage data (by running a Notebook file).
4. Running the transformation pipelines (Silver & Gold ETL) conditioned on the dependency (`depends_on`) on the success of all extraction tasks.
5. Refreshing the dashboard (Dashboard Refresh).
* **System Resiliency Settings:**
* **Retries:** The system was configured to retry 4 times in case any task fails.
* **Scheduling:** Tasks are scheduled to run periodically using Cron Syntax.
* **Notifications:** Email notifications enabled for cases of success, failure, or delay.

This platform was designed and built as part of developing an advanced cloud infrastructure. The project focuses on applying DataOps best practices, writing clean and efficient PySpark code, and designing scalable engineering database systems in Cairo's tech environment to serve advanced business intelligence goals.
