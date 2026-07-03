from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.table(
    name="retail_project.retail_silver.product_catalog",
    comment="Standardized and quality-checked product catalog from bronze layer",
    cluster_by=["category", "subcategory"]
)
@dp.expect_or_drop("valid_product_id", "product_id IS NOT NULL AND TRIM(product_id) != ''")
@dp.expect_or_drop("valid_product_name", "product_name IS NOT NULL AND TRIM(product_name) != ''")
@dp.expect_or_drop("valid_price", "unit_price >= 0")
@dp.expect("valid_launch_date", "launch_date IS NULL OR launch_date <= CURRENT_DATE()")
@dp.expect("valid_updated_at", "updated_at IS NOT NULL")
def product_catalog_silver():
    """
    Silver layer transformation for product catalog.
    Applies standardization and data quality rules.
    """
    return (
        spark.readStream.table("retail_project.postgress_bronze.product_catalog")
        # Standardization: trim and clean string fields
        .withColumn("product_id", F.trim(F.col("product_id")))
        .withColumn("product_name", F.trim(F.col("product_name")))
        .withColumn("category", F.upper(F.trim(F.col("category"))))
        .withColumn("subcategory", F.upper(F.trim(F.col("subcategory"))))
        .withColumn("brand", F.trim(F.col("brand")))
        .withColumn("supplier_name", F.trim(F.col("supplier_name")))
        
        # Standardization: ensure consistent null handling for optional fields
        .withColumn("brand", F.when(F.col("brand") == "", None).otherwise(F.col("brand")))
        .withColumn("supplier_name", F.when(F.col("supplier_name") == "", None).otherwise(F.col("supplier_name")))
        
        # Standardization: add processing metadata
        .withColumn("processed_at", F.current_timestamp())
        
        # Select final columns (excluding SCD columns from bronze if not needed)
        .select(
            "product_id",
            "product_name",
            "category",
            "subcategory",
            "brand",
            "unit_price",
            "supplier_name",
            "launch_date",
            "is_active",
            "updated_at",
            "processed_at"
        )
    )
