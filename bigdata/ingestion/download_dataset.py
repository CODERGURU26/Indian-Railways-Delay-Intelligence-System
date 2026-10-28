from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq


DATASET_NAME = "pjay-in/indian-railways-delays"
DATASET_API = f"https://datasets-server.huggingface.co/parquet?dataset={urllib.parse.quote(DATASET_NAME, safe='')}"
SIZE_API = f"https://datasets-server.huggingface.co/size?dataset={urllib.parse.quote(DATASET_NAME, safe='')}"
SOURCE_URL = f"https://huggingface.co/datasets/{DATASET_NAME}"
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SAMPLE_DIR = ROOT / "data" / "sample"
MANIFEST_PATH = ROOT / "data" / "manifest.json"


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "railway-delay-intelligence/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "railway-delay-intelligence/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            try:
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)
                temporary.flush()
                os.fsync(temporary.fileno())
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise
    temporary_path.replace(target)


def import_dataset(config: str) -> dict:
    shard_response = fetch_json(DATASET_API)
    shards = [
        item for item in shard_response["parquet_files"]
        if item["config"] == config and item["split"] == "train"
    ]
    if not shards:
        available = sorted({item["config"] for item in shard_response["parquet_files"]})
        raise ValueError(f"No train Parquet shards found for {config!r}; available configs: {available}")

    size_response = fetch_json(SIZE_API)
    config_size = next(
        (item for item in size_response["size"]["configs"] if item["config"] == config),
        None,
    )
    if config_size is None:
        raise ValueError(f"Hugging Face did not report row-count metadata for config {config!r}")
    expected_rows = int(config_size["num_rows"])

    output_dir = RAW_DIR / config
    files = []
    total_rows = 0
    total_bytes = 0
    for shard in sorted(shards, key=lambda item: item["filename"]):
        source_name = shard["filename"]
        target = output_dir / source_name
        if not target.is_file() or target.stat().st_size != int(shard["size"]):
            download_file(shard["url"], target)
        actual_bytes = target.stat().st_size
        if actual_bytes != int(shard["size"]):
            raise RuntimeError(
                f"Downloaded size mismatch for {source_name}: "
                f"expected {shard['size']} bytes, got {actual_bytes}"
            )
        rows = pq.read_metadata(target).num_rows
        total_rows += rows
        total_bytes += actual_bytes
        files.append({
            "name": source_name,
            "path": str(target),
            "rows": rows,
            "bytes": actual_bytes,
            "sha256": sha256_file(target),
        })

    if total_rows != expected_rows:
        raise RuntimeError(
            f"Row-count mismatch for {config}: Hugging Face reports {expected_rows}, "
            f"downloaded Parquet files contain {total_rows}"
        )

    manifest = {
        "dataset": DATASET_NAME,
        "config": config,
        "split": "train",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "row_count": total_rows,
        "expected_row_count": expected_rows,
        "shard_count": len(files),
        "total_bytes": total_bytes,
        "source_url": SOURCE_URL,
        "license": "cc-by-4.0",
        "files": files,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and verify every Parquet shard for a Hugging Face dataset config."
    )
    parser.add_argument("--config", default="2026-10-10_", help="Hugging Face dataset config name.")
    args = parser.parse_args()

    try:
        manifest = import_dataset(args.config)
        print(json.dumps(manifest, indent=2))
    except Exception as exc:  # pragma: no cover
        print(json.dumps({
            "status": "download_failed",
            "error": str(exc),
            "dataset": DATASET_NAME,
            "config": args.config,
        }, indent=2))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
