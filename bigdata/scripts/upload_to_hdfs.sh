#!/usr/bin/env bash
set -euo pipefail

HDFS_INPUT="/railway/raw"
HDFS_OUTPUT="/railway/processed"
LOCAL_FILE="$(dirname "$0")/../data/processed/railway_sample.csv"

hdfs dfs -mkdir -p "$HDFS_INPUT" "$HDFS_OUTPUT"
hdfs dfs -put -f "$LOCAL_FILE" "$HDFS_INPUT/railway_sample.csv"
echo "Uploaded sample CSV to $HDFS_INPUT/railway_sample.csv"
