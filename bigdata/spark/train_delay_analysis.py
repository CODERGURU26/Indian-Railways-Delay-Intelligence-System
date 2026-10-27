from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "sample"
OUTPUT_PATH = ROOT / "data" / "processed" / "spark_outputs"


def main() -> None:
    spark = SparkSession.builder.appName("railway-delay-analysis").getOrCreate()

    parquet_files = list((RAW_PATH).glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files were found under {RAW_PATH}")

    df = spark.read.option("mergeSchema", "true").parquet(*[str(path) for path in parquet_files])

    summary = (
        df.filter(F.col("arrival_delay_min").isNotNull())
        .groupBy("train_number")
        .agg(
            F.avg("arrival_delay_min").alias("avg_arrival_delay_min"),
            F.max("arrival_delay_min").alias("max_arrival_delay_min"),
            F.count("*").alias("record_count"),
        )
        .orderBy(F.col("avg_arrival_delay_min").desc())
    )

    summary.write.mode("overwrite").parquet(str(OUTPUT_PATH / "train_delay_summary"))
    print("Saved Spark summary to", OUTPUT_PATH / "train_delay_summary")


if __name__ == "__main__":
    main()
