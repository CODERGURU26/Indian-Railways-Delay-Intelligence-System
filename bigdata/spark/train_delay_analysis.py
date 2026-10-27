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

    arrival = df.filter(F.col("arrival_delay_min").isNotNull())

    journey_delays = (
        arrival.groupBy("train_number", "start_date")
        .agg(F.avg("arrival_delay_min").alias("journey_avg_arrival_delay_min"))
    )
    train_summary = (
        journey_delays.groupBy("train_number")
        .agg(
            F.avg("journey_avg_arrival_delay_min").alias("avg_arrival_delay_min"),
            F.max("journey_avg_arrival_delay_min").alias("max_journey_avg_arrival_delay_min"),
            F.count("*").alias("journey_count"),
        )
        .orderBy(F.col("avg_arrival_delay_min").desc())
    )

    summaries = {
        "train_delay_summary": train_summary,
        "station_delay_summary": (
            df.groupBy("station_code")
            .agg(
                F.avg("arrival_delay_min").alias("avg_arrival_delay_min"),
                F.avg("departure_delay_min").alias("avg_departure_delay_min"),
                F.count("*").alias("stop_record_count"),
            )
        ),
        "category_delay_summary": (
            df.groupBy("category")
            .agg(
                F.avg("arrival_delay_min").alias("avg_arrival_delay_min"),
                F.avg("departure_delay_min").alias("avg_departure_delay_min"),
                F.count("*").alias("stop_record_count"),
            )
        ),
        "date_delay_summary": (
            df.groupBy("start_date")
            .agg(
                F.avg("arrival_delay_min").alias("avg_arrival_delay_min"),
                F.avg("departure_delay_min").alias("avg_departure_delay_min"),
                F.count("*").alias("stop_record_count"),
            )
            .orderBy("start_date")
        ),
        "service_status_summary": (
            df.groupBy("status")
            .agg(
                F.countDistinct(F.struct("train_number", "start_date")).alias("journey_count")
            )
        ),
        "stop_sequence_delay_summary": (
            arrival.groupBy("seq")
            .agg(
                F.avg("arrival_delay_min").alias("avg_arrival_delay_min"),
                F.count("*").alias("observation_count"),
            )
            .orderBy("seq")
        ),
    }

    for name, summary in summaries.items():
        target = OUTPUT_PATH / name
        summary.write.mode("overwrite").parquet(str(target))
        print("Saved Spark summary to", target)

    ordered_stops = F.array_sort(F.collect_list(F.struct("seq", "station_code")))
    route_summary = (
        df.groupBy("train_number", "start_date")
        .agg(
            F.concat_ws(" -> ", F.transform(ordered_stops, lambda stop: stop["station_code"])).alias("route"),
            F.avg("arrival_delay_min").alias("avg_arrival_delay_min"),
        )
        .groupBy("route")
        .agg(
            F.avg("avg_arrival_delay_min").alias("avg_arrival_delay_min"),
            F.count("*").alias("journey_count"),
        )
        .orderBy(F.col("avg_arrival_delay_min").desc())
    )
    route_target = OUTPUT_PATH / "route_delay_summary"
    route_summary.write.mode("overwrite").parquet(str(route_target))
    print("Saved Spark summary to", route_target)


if __name__ == "__main__":
    main()
