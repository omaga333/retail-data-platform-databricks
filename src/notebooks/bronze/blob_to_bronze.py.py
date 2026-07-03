# Read CSV files using Auto Loader
df = (spark.readStream
  .format("cloudFiles")
  .option("cloudFiles.format", "csv")
  .option("cloudFiles.schemaLocation", "/Volumes/retail_project/volume/blob_s/transactions_s/_schema")
  .option("header", "true")
  .option("inferSchema", "true")
  .load("/Volumes/retail_project/volume/blob_s/transactions_s/")
)

# Write to bronze table
(df.writeStream
  .option("checkpointLocation", "/Volumes/retail_project/volume/blob_s/transactions_s/_checkpoint")
  .option("mergeSchema", "true")
  .trigger(availableNow=True)
  .toTable("retail_project.blob_storge.transactions")
)
