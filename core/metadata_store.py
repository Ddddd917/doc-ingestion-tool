import json
from pathlib import Path

from core.config import KNOWLEDGE_BASE_ROOT

METADATA_FILE = KNOWLEDGE_BASE_ROOT / "metadata.json"


def load_metadata() -> list[dict]:
    if not METADATA_FILE.exists():
        return []
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_metadata(records: list):
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def add_record(record: dict):
    records = load_metadata()
    records.append(record)
    save_metadata(records)


def get_records_by_domain(domain: str) -> list[dict]:
    records = load_metadata()
    return [
        r for r in records
        if any(d.get("name") == domain for d in r.get("domains", []))
    ]


def update_record(file_path: str, updates: dict):
    records = load_metadata()
    for r in records:
        if r.get("file_path") == file_path:
            r.update(updates)
            break
    save_metadata(records)


def delete_record(file_path: str):
    records = load_metadata()
    records = [r for r in records if r.get("file_path") != file_path]
    save_metadata(records)


def get_records_by_primary_domain(domain: str) -> list[dict]:
    records = load_metadata()
    return [
        r for r in records
        if r.get("domains") and r["domains"][0].get("name") == domain
    ]


def get_records_by_related_domain(domain: str) -> list[dict]:
    records = load_metadata()
    return [
        r for r in records
        if r.get("domains")
        and r["domains"][0].get("name") != domain
        and any(d.get("name") == domain for d in r["domains"][1:])
    ]
