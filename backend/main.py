import json
import os
import random
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Location API")

LOCATIONS = {
    "강남": {"lat": 37.4979, "lon": 127.0276},
    "여의도": {"lat": 37.5219, "lon": 126.9245},
    "마포": {"lat": 37.5663, "lon": 126.9014},
    "울산": {"lat": 35.5384, "lon": 129.3114},
    "광주": {"lat": 35.1595, "lon": 126.8526},
    "충청": {"lat": 36.6357, "lon": 127.4917},
    "강릉": {"lat": 37.7519, "lon": 128.8761},
    "제주": {"lat": 33.4996, "lon": 126.5312},
}

DATA_FILE = Path(__file__).parent / "data" / "records.jsonl"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)


class RecordIn(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=20)
    region: str
    score: int = Field(..., ge=1, le=5)
    memo: str = Field("", max_length=100)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/locations")
def get_locations():
    return LOCATIONS


@app.get("/locations/{name}")
def get_location(name: str):
    if name not in LOCATIONS:
        raise HTTPException(status_code=404, detail="location not found")
    return LOCATIONS[name]


@app.post("/records", status_code=201)
def create_record(record_in: RecordIn):
    if record_in.region not in LOCATIONS:
        raise HTTPException(status_code=400, detail="region not found")

    base = LOCATIONS[record_in.region]
    record = {
        "id": uuid.uuid4().hex[:8],
        "user_name": record_in.user_name,
        "region": record_in.region,
        "score": record_in.score,
        "memo": record_in.memo,
        "lat": base["lat"] + random.uniform(-0.01, 0.01),
        "lon": base["lon"] + random.uniform(-0.01, 0.01),
        "created_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
    }

    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


@app.get("/records")
def get_records():
    records = []
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    records.reverse()
    return {"count": len(records), "records": records}


@app.get("/stats")
def get_stats():
    records = []
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    if not records:
        return {"total": 0, "user_count": 0, "overall_avg": 0, "by_region": []}

    total = len(records)
    user_count = len({r["user_name"] for r in records})
    overall_avg = round(sum(r["score"] for r in records) / total, 1)

    by_region_map: dict[str, list[int]] = {}
    for r in records:
        by_region_map.setdefault(r["region"], []).append(r["score"])

    by_region = [
        {
            "region": region,
            "count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 1),
        }
        for region, scores in by_region_map.items()
    ]
    by_region.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total": total,
        "user_count": user_count,
        "overall_avg": overall_avg,
        "by_region": by_region,
    }


@app.delete("/records/{record_id}")
def delete_record(record_id: str):
    records = []
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    remaining = [r for r in records if r.get("id") != record_id]

    if len(remaining) == len(records):
        raise HTTPException(status_code=404, detail="record not found")

    fd, tmp_path = tempfile.mkstemp(dir=DATA_FILE.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for r in remaining:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp_path, DATA_FILE)
    except Exception:
        os.remove(tmp_path)
        raise

    return {"deleted": record_id}


@app.get("/records/user/{user_name}")
def get_records_by_user(user_name: str):
    records = []
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    if record.get("user_name") == user_name:
                        records.append(record)

    records.reverse()

    if not records:
        return {"user_name": user_name, "count": 0, "avg_score": 0, "records": []}

    avg_score = round(sum(r["score"] for r in records) / len(records), 1)
    return {
        "user_name": user_name,
        "count": len(records),
        "avg_score": avg_score,
        "records": records,
    }
