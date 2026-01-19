from __future__ import annotations

import os
from pathlib import Path

# Root of the repository (../ from app/)
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------
# Data locations
# ---------------------------------------------------------------------
# You can override these with environment variables in production.
# - PENDANTS_DIR must contain the source .3dm pendant files.
# - GLB_OUTPUT_DIR is where generated .glb files are cached.
# - METADATA_DIR is optional; reserved for future (e.g. pendant dimensions).
PENDANTS_DIR = Path(os.getenv("PENDANTS_DIR", str(BASE_DIR / "models" / "pendants")))
GLB_OUTPUT_DIR = Path(os.getenv("GLB_OUTPUT_DIR", str(BASE_DIR / "models" / "glb")))
METADATA_DIR = Path(os.getenv("METADATA_DIR", str(BASE_DIR / "metadata")))


# ---------------------------------------------------------------------
# Canopy specifications (physical dimensions in mm)
# ---------------------------------------------------------------------
# Matches v3 semantics (small vs large) and adds an explicit medium size.
CANOPY_SPECS = {
    "s": {
        "outer_radius_mm": 150,
        "inner_radius_mm": 130,
        "cable_offset_mm": 20,
        "height_mm": 40,
        "plate_thickness_mm": 1.5,
    },
    "m": {
        "outer_radius_mm": 300,
        "inner_radius_mm": 280,
        "cable_offset_mm": 30,
        "height_mm": 40,
        "plate_thickness_mm": 1.5,
    },
    "l": {
        "outer_radius_mm": 450,
        "inner_radius_mm": 430,
        "cable_offset_mm": 30,
        "height_mm": 40,
        "plate_thickness_mm": 1.5,
    },
}

# Cable appearance geometry.
CABLE_RADIUS_MM = 2.5

# Collision tuning (conservative defaults)
PENDANT_CLEARANCE_MM = -10.0



# ---------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------
# Allowed values: "development", "production"
ENV = os.getenv("ENV", "development").strip().lower()

# ---------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------
CORS_ORIGINS = {
    "development": [
        "https://newpg-dev.graypants.eu",
    ],
    "production": [
        "https://graypants.eu",
    ],
}

ALLOWED_CORS_ORIGINS = CORS_ORIGINS.get(ENV, [])


# ---------------------------------------------------------------------
# Static cache policy
# ---------------------------------------------------------------------
# Hashed GLB filenames are immutable, so they can be cached aggressively.
GLB_CACHE_CONTROL = (
    "public, max-age=31536000, immutable"
    if ENV == "production"
    else "public, max-age=3600"
)