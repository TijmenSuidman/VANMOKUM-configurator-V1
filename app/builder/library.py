from __future__ import annotations

from pathlib import Path
from typing import Dict

from app.settings import PENDANTS_DIR

# Pendant keys must match .3dm filenames (without extension).
PENDANT_LIBRARY: Dict[str, Dict] = {
    "denny": {"path": PENDANTS_DIR / "Denny.3dm"},
    "alki": {"path": PENDANTS_DIR / "Alki.3dm"},
    "allyn": {"path": PENDANTS_DIR / "Allyn.3dm"},
    "madison": {"path": PENDANTS_DIR / "Madison.3dm"},
    #"oliv": {"path": PENDANTS_DIR / "Oliv.3dm"},
    "moon10": {"path": PENDANTS_DIR / "Moon10.3dm"},
    "moon14": {"path": PENDANTS_DIR / "Moon14.3dm"},
    "moon18": {"path": PENDANTS_DIR / "Moon18.3dm"},
    "moon24": {"path": PENDANTS_DIR / "Moon24.3dm"},
    #"moon32": {"path": PENDANTS_DIR / "Moon32.3dm"},
    "nest24": {"path": PENDANTS_DIR / "Nest24.3dm"},
    "nest32": {"path": PENDANTS_DIR / "Nest32.3dm"},
    "hive9": {"path": PENDANTS_DIR / "Hive9.3dm"},
    "hive12": {"path": PENDANTS_DIR / "Hive12.3dm"},
    "hive15": {"path": PENDANTS_DIR / "Hive15.3dm"},
    "drop18": {"path": PENDANTS_DIR / "Drop18.3dm"},
    "drop26": {"path": PENDANTS_DIR / "Drop26.3dm"},
    "disc16": {"path": PENDANTS_DIR / "Disc16.3dm"},
    "disc20": {"path": PENDANTS_DIR / "Disc20.3dm"},
    "disc24": {"path": PENDANTS_DIR / "Disc24.3dm"},
    #"disc32": {"path": PENDANTS_DIR / "Disc32.3dm"},
    "bell10": {"path": PENDANTS_DIR / "Bell10.3dm"},
    "bell16": {"path": PENDANTS_DIR / "Bell16.3dm"},
    "ausi8": {"path": PENDANTS_DIR / "Ausi8.3dm"},
    "ausi12": {"path": PENDANTS_DIR / "Ausi12.3dm"},
    "ausi14": {"path": PENDANTS_DIR / "Ausi14.3dm"},
    
    
}


def get_pendant_path(key: str) -> Path:
    try:
        return Path(PENDANT_LIBRARY[key]["path"])
    except KeyError:
        raise ValueError(f"Unknown pendant model '{key}'")
