#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAPREDUCE_DIR="$ROOT/hadoop/mapreduce"
JAR_PATH="$MAPREDUCE_DIR/target/railway-delay-mapreduce-1.0.0.jar"
INPUT="/railway/raw/railway_sample.csv"
OUTPUT="/railway/processed/delay_summary"

if [[ ! -f "$JAR_PATH" ]]; then
  echo "JAR not found at $JAR_PATH. Build it with: mvn -f "$MAPREDUCE_DIR/pom.xml" package"
  exit 1
fi

hdfs dfs -rm -r -f "$OUTPUT"
hadoop jar "$JAR_PATH" com.example.railway.DelaySummaryJob "$INPUT" "$OUTPUT"
hdfs dfs -cat "$OUTPUT/part-r-00000"
