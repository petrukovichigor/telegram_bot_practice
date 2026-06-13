import json
import os
import tempfile
from threading import Lock
from typing import Optional


_LOCK = Lock()
_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_profiles.json")


def _load_all(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
    return data if isinstance(data, dict) else {}


def _atomic_write_json(path: str, data: dict) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="user_profiles_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass


def get_user_fio(user_id: int, path: str = _DEFAULT_PATH) -> Optional[str]:
    with _LOCK:
        data = _load_all(path)
        fio = data.get(str(user_id))
        return fio if isinstance(fio, str) and fio.strip() else None


def set_user_fio(user_id: int, fio: str, path: str = _DEFAULT_PATH) -> None:
    fio = fio.strip()
    if not fio:
        raise ValueError("fio must be non-empty")
    with _LOCK:
        data = _load_all(path)
        data[str(user_id)] = fio
        _atomic_write_json(path, data)

