from __future__ import annotations

from typing import List, Tuple

from app.schema import (
    ClusterConfig,
    CanopyConfig,
    CableConfig,
    LayoutConfig,
    PendantConfig,
    ClusterType,
)

# ---------------------------------------------------------------------
# Mapping tables (frozen public API)
# ---------------------------------------------------------------------

CANOPY_SIZE_MAP = {
    0: "s",
    1: "m",
    2: "l",
}
CANOPY_SIZE_REVERSE = {v: k for k, v in CANOPY_SIZE_MAP.items()}

CANOPY_APPEARANCE_MAP = {
    0: "canopy_black",
    1: "canopy_white",
}
CANOPY_APPEARANCE_REVERSE = {v: k for k, v in CANOPY_APPEARANCE_MAP.items()}

CABLE_APPEARANCE_MAP = {
    0: "cable_black",
    1: "cable_white",
}
CABLE_APPEARANCE_REVERSE = {v: k for k, v in CABLE_APPEARANCE_MAP.items()}

SHADE_APPEARANCE_MAP = {
    0: "shade_natural",
    1: "shade_blonde",
    2: "shade_white",
}
SHADE_APPEARANCE_REVERSE = {v: k for k, v in SHADE_APPEARANCE_MAP.items()}

CLUSTER_TYPE_MAP = {
    0: ClusterType.RING,
    1: ClusterType.RING_WITH_CENTER,
    2: ClusterType.RANDOM_RING,
}
CLUSTER_TYPE_REVERSE = {v: k for k, v in CLUSTER_TYPE_MAP.items()}

# Pendant model IDs must be stable (public API).
PENDANT_MODEL_MAP = {
    0: "denny",
    1: "alki",
    2: "allyn",
    3: "madison",
    4: "oliv",
    5: "moon10",
    6: "moon14",
    7: "moon18",
    8: "moon24",
    9: "moon32",
    10: "nest24",
    11: "nest32",
    12: "hive9",
    13: "hive12",
    14: "hive15",
    15: "drop18",
    16: "drop26",
    17: "disc16",
    18: "disc20",
    19: "disc24",
    20: "disc32",
    21: "bell10",
    22: "bell16",
    23: "ausi8",
    24: "ausi12",
    25: "ausi14",
}
PENDANT_MODEL_REVERSE = {v: k for k, v in PENDANT_MODEL_MAP.items()}


# ---------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------

def encode_config_to_code(config: ClusterConfig) -> str:
    """
    Compact, URL-safe encoding.

    Segments separated by '.', each segment begins with a prefix letter:
    - C: Canopy.      C{sizeId}{appearanceId}
    - L: Layout.      L{typeId}{firstDrop}{totalDrop} (drops in 100mm units; firstDrop is 2 digits)
    - B: Cable.       B{appearanceId}
    - P: Pendants.    P{count}-{modelId,shadeId}-{modelId,shadeId}-...
    - G: Global seed. G{seed}
    """
    size_id = CANOPY_SIZE_REVERSE[config.canopy.size]
    canopy_app_id = CANOPY_APPEARANCE_REVERSE[config.canopy.appearance]
    canopy_seg = f"C{size_id}{canopy_app_id}"

    type_id = CLUSTER_TYPE_REVERSE[config.layout.cluster_type]
    first_u = int(round(config.layout.first_drop_mm / 100))
    total_u = int(round(config.layout.total_drop_mm / 100))
    if not (0 <= first_u <= 99):
        raise ValueError("layout.first_drop_mm out of encodable range.")
    if not (0 <= total_u <= 999):
        raise ValueError("layout.total_drop_mm out of encodable range.")
    layout_seg = f"L{type_id}{first_u:02d}{total_u:03d}"

    cable_id = CABLE_APPEARANCE_REVERSE[config.cable.appearance]
    cable_seg = f"B{cable_id}"

    pendant_items: List[str] = []
    for p in config.pendants:
        model_id = PENDANT_MODEL_REVERSE[p.model]
        shade_id = SHADE_APPEARANCE_REVERSE[p.appearance]
        pendant_items.append(f"{model_id},{shade_id}")
    pendant_seg = f"P{len(pendant_items)}-" + "-".join(pendant_items)

    global_seg = f"G{int(config.random_seed)}"

    return ".".join([canopy_seg, layout_seg, cable_seg, pendant_seg, global_seg])


# ---------------------------------------------------------------------
# Decoding
# ---------------------------------------------------------------------

def decode_code_to_config(code: str) -> ClusterConfig:
    """
    Decode a configuration code into a validated ClusterConfig.
    """
    if not code or not isinstance(code, str):
        raise ValueError("Empty configuration code.")

    segments = [s for s in code.split(".") if s]

    canopy = None
    layout = None
    cable = None
    pendants: List[PendantConfig] = []
    random_seed = 0
    defaults_applied: List[str] = []

    for seg in segments:
        prefix = seg[0]
        body = seg[1:]

        if prefix == "C":
            if len(body) < 2:
                raise ValueError("Malformed canopy segment (C).")
            size_id = int(body[0])
            appearance_id = int(body[1:])
            canopy = CanopyConfig(
                size=CANOPY_SIZE_MAP[size_id],
                appearance=CANOPY_APPEARANCE_MAP[appearance_id],
            )

        elif prefix == "L":
            if len(body) < 1 + 2 + 1:
                raise ValueError("Malformed layout segment (L).")
            t = int(body[0])
            f = int(body[1:3]) * 100
            d = int(body[3:]) * 100
            layout = LayoutConfig(
                cluster_type=CLUSTER_TYPE_MAP[t],
                first_drop_mm=f,
                total_drop_mm=d,
            )

        elif prefix == "B":
            appearance_id = int(body)
            cable = CableConfig(appearance=CABLE_APPEARANCE_MAP[appearance_id])

        elif prefix == "P":
            try:
                count_part, items_part = body.split("-", 1)
                count = int(count_part)
                item_tokens = items_part.split("-") if items_part else []
            except ValueError:
                raise ValueError("Malformed pendant segment (P).")

            if count != len(item_tokens):
                raise ValueError("Pendant count does not match entries.")

            pendants.clear()
            for token in item_tokens:
                try:
                    model_id_str, shade_id_str = token.split(",", 1)
                    model_id = int(model_id_str)
                    shade_id = int(shade_id_str)
                except ValueError:
                    raise ValueError("Malformed pendant entry.")

                pendants.append(
                    PendantConfig(
                        model=PENDANT_MODEL_MAP[model_id],
                        appearance=SHADE_APPEARANCE_MAP[shade_id],
                    )
                )

        elif prefix == "G":
            random_seed = int(body)

        else:
            # Ignore unknown segments for forward compatibility.
            continue

    if canopy is None:
        raise ValueError("Missing canopy segment (C).")

    if layout is None:
        layout = LayoutConfig()
        defaults_applied.append("layout defaulted")

    if cable is None:
        cable = CableConfig()
        defaults_applied.append("cable defaulted")

    if not pendants:
        raise ValueError("At least one pendant must be specified.")

    return ClusterConfig(
        canopy=canopy,
        cable=cable,
        layout=layout,
        pendants=pendants,
        random_seed=random_seed,
        defaults_applied=defaults_applied,
    )


def decode_code_to_hash_inputs(code: str) -> Tuple[str, ClusterConfig]:
    """Helper for API: decode and re-encode to a canonical code string."""
    config = decode_code_to_config(code)
    canonical_code = encode_config_to_code(config)
    return canonical_code, config
