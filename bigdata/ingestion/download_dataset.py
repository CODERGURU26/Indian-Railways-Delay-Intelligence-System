from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from datasets import load_dataset
except Exception as exc:  # pragma: no cover
    load_dataset = None
    DATASET_IMPORT_ERROR = exc
else:
    DATASET_IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SAMPLE_DIR = ROOT / "data" / "sample"
MANIFEST_PATH = ROOT / "data" / "manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_directories() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def import_dataset(config: str, limit: int | None = None) -> dict:
    if load_dataset is None:
        raise RuntimeError(f"datasets import failed: {DATASET_IMPORT_ERROR}")

    dataset_name = "pjay-in/indian-railways-delays"
    split = "train"
    if limit is not None:
        split = f"train[:{limit}]"

    loaded = load_dataset(dataset_name, config, split=split)
    table = loaded.to_pandas()
    target = SAMPLE_DIR / f"{config.replace('/', '_')}_sample.parquet"
    table.to_parquet(target, index=False)

    manifest = {
        "dataset": dataset_name,
        "config": config,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "row_count": int(len(table)),
        "source_url": "https://huggingface.co/datasets/pjay-in/indian-railways-delays",
        "license": "cc-by-4.0",
        "file": {
            "name": target.name,
            "path": str(target),
            "sha256": sha256_file(target),
            "rows": int(len(table)),
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a sample of the Indian Railways delay dataset.")
    parser.add_argument("--config", default="2026-10-10_", help="Dataset config name from the Hugging Face dataset card.")
    parser.add_argument("--limit", type=int, default=5000, help="How many rows to include in the sample parquet file.")
    args = parser.parse_args()

    ensure_directories()
    try:
        manifest = import_dataset(args.config, args.limit)
        print(json.dumps(manifest, indent=2))
    except Exception as exc:  # pragma: no cover
        message = {
            "status": "download_failed",
            "error": str(exc),
            "dataset": "pjay-in/indian-railways-delays",
            "config": args.config,
        }
        print(json.dumps(message, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
