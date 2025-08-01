from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, avg, stddev, expr, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
import duckdb

# Define schema for Binance trade events
schema = StructType([
    StructField('e', StringType()),
    StructField('E', LongType()),
    StructField('s', StringType()),
    StructField('t', LongType()),
    StructField('p', StringType()),  # price as string
    StructField('q', StringType()),  # quantity as string
    StructField('b', LongType()),
    StructField('a', LongType()),
    StructField('T', LongType()),
    StructField('m', StringType()),
    StructField('M', StringType()),
])

spark = SparkSession.builder \
    .appName("CryptoKafkaSparkStreaming") \
    .config("spark.driver.extraJavaOptions", "--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.util.concurrent=ALL-UNNAMED --add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.cs=ALL-UNNAMED --add-opens=java.base/sun.security.action=ALL-UNNAMED --add-opens=java.base/sun.security.util=ALL-UNNAMED --add-opens=java.base/javax.security.auth=ALL-UNNAMED") \
    .config("spark.executor.extraJavaOptions", "--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.util.concurrent=ALL-UNNAMED --add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.cs=ALL-UNNAMED --add-opens=java.base/sun.security.action=ALL-UNNAMED --add-opens=java.base/sun.security.util=ALL-UNNAMED --add-opens=java.base/javax.security.auth=ALL-UNNAMED") \
    .getOrCreate()

# Read from Kafka
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "trades") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON
json_df = raw_df.select(from_json(col("value"), schema).alias("data")).select("data.*")

# Convert price to double and timestamp to timestamp
trades_df = json_df.withColumn("price", col("p").cast(DoubleType())) \
                   .withColumn("timestamp", (col("T")/1000).cast("timestamp"))

# Compute moving average, price change %, and volatility over 1-minute window
agg_df = trades_df \
    .withWatermark("timestamp", "2 minutes") \
    .groupBy(window(col("timestamp"), "1 minute")) \
    .agg(
        avg("price").alias("avg_price"),
        (expr("(max(price)-min(price))/min(price)*100")).alias("price_change_pct"),
        stddev("price").alias("volatility")
    )

# Write raw data to Parquet
raw_query = trades_df.writeStream \
    .format("parquet") \
    .option("path", "storage/raw_parquet/") \
    .option("checkpointLocation", "storage/checkpoints/raw/") \
    .outputMode("append") \
    .start()

# Write aggregates to DuckDB using foreachBatch
DUCKDB_PATH = "storage/analytics.duckdb"

def write_to_duckdb(batch_df, batch_id):
    batch_pd = batch_df.toPandas()
    if not batch_pd.empty:
        con = duckdb.connect(DUCKDB_PATH)
        con.execute("CREATE TABLE IF NOT EXISTS analytics (window_start TIMESTAMP, window_end TIMESTAMP, avg_price DOUBLE, price_change_pct DOUBLE, volatility DOUBLE)")
        con.execute("INSERT INTO analytics SELECT * FROM batch_df", {'batch_df': batch_pd})
        con.close()

agg_query = agg_df.writeStream \
    .foreachBatch(write_to_duckdb) \
    .outputMode("update") \
    .option("checkpointLocation", "storage/checkpoints/agg/") \
    .start()

spark.streams.awaitAnyTermination() 