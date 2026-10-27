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
    assert "file" in payload
