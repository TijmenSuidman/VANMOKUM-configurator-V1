# materials.py
# NO TEXTURES. Pure PBR baseColorFactor + metallic/roughness.

def normalize_canopy_color(token: str) -> str:
    token = (token or "").lower().strip()
    if token in ("white", "canopy_white", "w"):
        return "canopy_white"
    return "canopy_black"


def normalize_cable_color(token: str) -> str:
    token = (token or "").lower().strip()
    if token in ("white", "cable_white", "w"):
        return "cable_white"
    return "cable_black"


def normalize_shade_color(token: str) -> str:
    token = (token or "").lower().strip()
    if token in ("white", "shade_white", "w"):
        return "shade_white"
    if token in ("blonde", "shade_blonde", "b"):
        return "shade_blonde"
    return "shade_natural"


MATERIAL_PRESETS = {
    "canopy_white": {
        "name": "CanopyWhite",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.95, 0.95, 0.95, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.6,
        },
    },
    "canopy_black": {
        "name": "CanopyBlack",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.05, 0.05, 0.05, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.65,
        },
    },
    "cable_white": {
        "name": "CableWhite",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.92, 0.92, 0.92, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.8,
        },
    },
    "cable_black": {
        "name": "CableBlack",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.03, 0.03, 0.03, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.85,
        },
    },

    # Shades: pure color. Tune these as needed.
    "shade_white": {
        "name": "ShadeWhite",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.82, 0.81, 0.78, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.95,
        },
    },
    "shade_blonde": {
        "name": "ShadeBlonde",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.48, 0.40, 0.26, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.95,
        },
    },
    "shade_natural": {
        "name": "ShadeNatural",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.13, 0.09, 0.05, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.98,
        },
    },
}


def get_material_preset(key: str, fallback: str = "shade_natural") -> dict:
    key = (key or "").strip()
    if key in MATERIAL_PRESETS:
        return MATERIAL_PRESETS[key]
    if fallback in MATERIAL_PRESETS:
        return MATERIAL_PRESETS[fallback]
    return MATERIAL_PRESETS["shade_natural"]
