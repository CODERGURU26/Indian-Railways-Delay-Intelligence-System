from __future__ import annotations

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"
CSV_TARGET = ROOT / "data" / "processed" / "railway_sample.csv"


if __name__ == "__main__":
    parquet_files = list(SAMPLE.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No sample parquet file found in bigdata/data/sample.")

    frames = [pd.read_parquet(path) for path in parquet_files]
    combined = pd.concat(frames, ignore_index=True)
    CSV_TARGET.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(CSV_TARGET, index=False)
    print(f"Wrote {len(combined)} rows to {CSV_TARGET}")
