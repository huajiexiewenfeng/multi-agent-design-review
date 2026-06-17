from collections.abc import Iterator
from contextlib import contextmanager
import json
from pathlib import Path
import threading

_LOCKS: dict[str, threading.Lock] = {}


@contextmanager
def run_lock(run_dir: Path) -> Iterator[None]:
    key = str(run_dir.resolve())
    lock = _LOCKS.setdefault(key, threading.Lock())
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
