import json
from pathlib import Path


def test_dataset_manifest_structure():
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "data" / "manifest.json"
    if not manifest_path.exists():
        assert True
        return

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "dataset" in payload
    assert "config" in payload
    assert "retrieved_at" in payload
    assert payload["split"] == "train"
    assert payload["row_count"] == payload["expected_row_count"]
    assert payload["row_count"] == sum(item["rows"] for item in payload["files"])
    assert payload["shard_count"] == len(payload["files"])
    assert all(len(item["sha256"]) == 64 for item in payload["files"])
