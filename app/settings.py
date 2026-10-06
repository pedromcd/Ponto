from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    database_path: Path
    face_threshold: float
    face_margin: float
    cooldown_seconds: int
    capture_count: int
    face_model: str
    det_size: int
    min_face_area: float
    face_models_dir: Path


def get_settings() -> Settings:
    db_value = os.getenv("PONTO_BANCO", "dados/ponto.db")
    db_path = Path(db_value)
    if not db_path.is_absolute():
        db_path = ROOT / db_path

    models_value = os.getenv("PONTO_MODELOS_DIR", "dados/modelos")
    models_path = Path(models_value)
    if not models_path.is_absolute():
        models_path = ROOT / models_path

    return Settings(
        database_path=db_path,
        face_threshold=_env_float("PONTO_LIMIAR", 0.45),
        face_margin=_env_float("PONTO_MARGEM", 0.06),
        cooldown_seconds=_env_int("PONTO_CARENCIA", 60),
        capture_count=_env_int("PONTO_CAPTURAS", 5),
        face_model=os.getenv("PONTO_MODELO", "buffalo_l"),
        det_size=_env_int("PONTO_DET_SIZE", 640),
        min_face_area=_env_float("PONTO_AREA_MIN", 0.020),
        face_models_dir=models_path,
    )
