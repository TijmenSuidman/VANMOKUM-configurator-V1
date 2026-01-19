from __future__ import annotations

from typing import List, Tuple

from app.schema import ClusterConfig
from app.builder.geometry import (
    build_canopy,
    place_pendants_then_plan_cables,
    build_cables_from_placements,
)


def build_mesh_groups(config: ClusterConfig) -> Tuple[List[dict], List[str]]:
    """
    Returns:
        mesh_groups: list of {"mesh": rhino3dm.Mesh, "material_key": str}
        material_keys: unique material keys used in this model
    """
    n = config.num_pendants

    bottom_mesh, top_mesh, connection_points = build_canopy(config.canopy.size, n, config.layout.cluster_type)

    # Key change vs v3: pendants are placed first, then cables are created.
    placements = place_pendants_then_plan_cables(config, connection_points)
    cable_meshes, _ = build_cables_from_placements(placements)

    mesh_groups: List[dict] = []

    # Canopy
    mesh_groups.append({"mesh": bottom_mesh, "material_key": config.canopy.appearance})
    mesh_groups.append({"mesh": top_mesh, "material_key": config.canopy.appearance})

    # Cables
    for cm in cable_meshes:
        mesh_groups.append({"mesh": cm, "material_key": config.cable.appearance})

    # Pendants
    for pl in placements:
        for pm in pl.meshes:
            mesh_groups.append({"mesh": pm, "material_key": pl.pendant.appearance})

    # Unique keys (stable ordering)
    material_keys: List[str] = []
    for mg in mesh_groups:
        k = mg["material_key"]
        if k not in material_keys:
            material_keys.append(k)

    return mesh_groups, material_keys
