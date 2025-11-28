"""Simple JSON-file backed storage for runs and job queue."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(os.getenv("DATA_DIR", "./data/state"))
RUNS_FILE = DATA_DIR / "runs.json"
JOBS_FILE = DATA_DIR / "jobs.json"
LOCK = threading.Lock()


def _ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not RUNS_FILE.exists():
        RUNS_FILE.write_text(json.dumps({}, indent=2))
    if not JOBS_FILE.exists():
        JOBS_FILE.write_text(json.dumps([], indent=2))


def load_runs() -> Dict[str, Dict[str, Any]]:
    _ensure_files()
    return json.loads(RUNS_FILE.read_text())


def save_runs(runs: Dict[str, Dict[str, Any]]) -> None:
    _ensure_files()
    RUNS_FILE.write_text(json.dumps(runs, indent=2))


def create_run(run_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    with LOCK:
        runs = load_runs()
        runs[run_id] = payload
        save_runs(runs)
        return payload


def update_run(run_id: str, **updates: Any) -> Dict[str, Any]:
    with LOCK:
        runs = load_runs()
        run = runs.get(run_id, {})
        run.update(updates)
        runs[run_id] = run
        save_runs(runs)
        return run


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    runs = load_runs()
    return runs.get(run_id)


def enqueue_job(job: Dict[str, Any]) -> None:
    with LOCK:
        _ensure_files()
        jobs = json.loads(JOBS_FILE.read_text())
        jobs.append(job)
        JOBS_FILE.write_text(json.dumps(jobs, indent=2))


def pop_job() -> Optional[Dict[str, Any]]:
    with LOCK:
        _ensure_files()
        jobs: List[Dict[str, Any]] = json.loads(JOBS_FILE.read_text())
        if not jobs:
            return None
        job = jobs.pop(0)
        JOBS_FILE.write_text(json.dumps(jobs, indent=2))
        return job
