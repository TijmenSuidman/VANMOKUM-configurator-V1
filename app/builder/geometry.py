from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List, Sequence, Tuple

import rhino3dm

from app.schema import ClusterConfig, ClusterType, PendantConfig
from app.settings import CANOPY_SPECS, CABLE_RADIUS_MM
from app.builder.library import get_pendant_path


# -------------------------------------------------------------#
# BASIC MESH HELPERS
# -------------------------------------------------------------#

def create_cylinder_mesh(radius: float, height: float, segments: int = 64) -> rhino3dm.Mesh:
    mesh = rhino3dm.Mesh()
    ring_bottom = []
    ring_top = []

    for i in range(segments):
        a = 2 * math.pi * i / segments
        ring_bottom.append(mesh.Vertices.Add(radius * math.cos(a), radius * math.sin(a), 0))
        ring_top.append(mesh.Vertices.Add(radius * math.cos(a), radius * math.sin(a), height))

    for i in range(segments):
        i2 = (i + 1) % segments
        mesh.Faces.AddFace(ring_bottom[i], ring_bottom[i2], ring_top[i2], ring_top[i])

    cb = mesh.Vertices.Add(0, 0, 0)
    ct = mesh.Vertices.Add(0, 0, height)

    for i in range(segments):
        i2 = (i + 1) % segments
        mesh.Faces.AddFace(cb, ring_bottom[i2], ring_bottom[i])
        mesh.Faces.AddFace(ct, ring_top[i], ring_top[i2])

    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


def _rotation_from_z(direction: rhino3dm.Vector3d) -> rhino3dm.Transform:
    z = rhino3dm.Vector3d(0, 0, 1)
    d = direction
    d.Unitize()

    dot = max(-1.0, min(1.0, z.X * d.X + z.Y * d.Y + z.Z * d.Z))

    if abs(dot - 1.0) < 1e-8:
        return rhino3dm.Transform.Identity
    if abs(dot + 1.0) < 1e-8:
        return rhino3dm.Transform.Rotation(
            math.pi, rhino3dm.Vector3d(1, 0, 0), rhino3dm.Point3d(0, 0, 0)
        )

    axis = rhino3dm.Vector3d.CrossProduct(z, d)
    angle = math.acos(dot)
    return rhino3dm.Transform.Rotation(angle, axis, rhino3dm.Point3d(0, 0, 0))



# -------------------------------------------------------------#
# CANOPY
# -------------------------------------------------------------#

def build_canopy(size_key: str, n_pendants: int, cluster_type: ClusterType):
    spec = CANOPY_SPECS[size_key]
    r_in = spec["inner_radius_mm"]
    r_out = spec["outer_radius_mm"]
    offset = spec["cable_offset_mm"]
    height = spec["height_mm"]
    plate = spec["plate_thickness_mm"]

    bottom = create_cylinder_mesh(r_out, plate, 96)
    bottom.Transform(rhino3dm.Transform.Translation(0, 0, -height))

    top = create_cylinder_mesh(r_in + plate, height - plate, 96)
    top.Transform(rhino3dm.Transform.Translation(0, 0, -(height - plate)))

    conn_r = r_in - offset
    zc = -height

    points: List[rhino3dm.Point3d] = []

    wants_center = cluster_type in (ClusterType.RING_WITH_CENTER, ClusterType.RANDOM_RING)

    if wants_center:
        ring_count = max(0, n_pendants - 1)
        for i in range(ring_count):
            a = 2 * math.pi * i / max(1, ring_count)
            points.append(rhino3dm.Point3d(conn_r * math.cos(a), conn_r * math.sin(a), zc))
        points.append(rhino3dm.Point3d(0, 0, zc))  # center always last
    else:
        # Spiral (RING): no center, all on the ring
        for i in range(n_pendants):
            a = 2 * math.pi * i / max(1, n_pendants)
            points.append(rhino3dm.Point3d(conn_r * math.cos(a), conn_r * math.sin(a), zc))

    return bottom, top, points


# -------------------------------------------------------------#
# PENDANTS
# -------------------------------------------------------------#

@lru_cache(maxsize=128)
def _load_pendant_meshes(model_key: str) -> Tuple[rhino3dm.Mesh, ...]:
    model = rhino3dm.File3dm.Read(str(get_pendant_path(model_key)))
    meshes = [obj.Geometry.Duplicate() for obj in model.Objects if isinstance(obj.Geometry, rhino3dm.Mesh)]
    return tuple(meshes)


@lru_cache(maxsize=128)
def _pendant_extents(model_key: str) -> Tuple[float, float]:
    meshes = _load_pendant_meshes(model_key)
    bbox = None
    for m in meshes:
        b = m.GetBoundingBox()
        bbox = b if bbox is None else rhino3dm.BoundingBox.Union(bbox, b)

    top = bbox.Max.Z
    bottom = -bbox.Min.Z
    return float(top), float(bottom)


@dataclass(frozen=True)
class PendantPlacement:
    pendant: PendantConfig
    start: rhino3dm.Point3d
    end: rhino3dm.Point3d
    meshes: Tuple[rhino3dm.Mesh, ...]


# -------------------------------------------------------------#
# CORE PLACEMENT LOGIC
# -------------------------------------------------------------#

def place_pendants_then_plan_cables(
    config: ClusterConfig,
    connection_points: Sequence[rhino3dm.Point3d],
) -> List[PendantPlacement]:

    n = len(config.pendants)
    rng = random.Random(int(config.random_seed))

    tops: List[float] = []
    bottoms: List[float] = []
    meshes_by_index: List[Tuple[rhino3dm.Mesh, ...]] = []

    for p in config.pendants:
        t, b = _pendant_extents(p.model)
        tops.append(t)
        bottoms.append(b)
        meshes_by_index.append(tuple(m.Duplicate() for m in _load_pendant_meshes(p.model)))

    first = float(config.layout.first_drop_mm)
    total = float(config.layout.total_drop_mm)

    occupied = tops[0] + bottoms[-1]
    for i in range(n - 1):
        occupied += bottoms[i] + tops[i + 1]

    available = total - first
    gap = 0.0 if n <= 1 else (available - occupied) / (n - 1)

    drops = [first]
    for i in range(n - 1):
        drops.append(drops[-1] + bottoms[i] + tops[i + 1] + gap)

    indices = list(range(n))
    if n > 1 and config.layout.cluster_type in (
        ClusterType.RING,
        ClusterType.RING_WITH_CENTER,
        ClusterType.RANDOM_RING,
    ):
        indices = sorted(
            range(n),
            key=lambda i: math.atan2(connection_points[i].Y, connection_points[i].X),
        )
        if config.layout.cluster_type == ClusterType.RANDOM_RING:
            rng.shuffle(indices)

    placements: List[PendantPlacement] = []

    for i in range(n):
        sp = connection_points[indices[i]]
        drop = drops[i]
        end = rhino3dm.Point3d(sp.X, sp.Y, sp.Z - drop)

        # Random twist around the cable axis (vertical Z in this setup).
        twist = rng.random() * (2.0 * math.pi)
        rot = rhino3dm.Transform.Rotation(
            twist,
            rhino3dm.Vector3d(0, 0, 1),
            rhino3dm.Point3d(0, 0, 0),
        )

        placed = []
        for m in meshes_by_index[i]:
            mm = m.Duplicate()
            mm.Transform(rot)
            mm.Transform(rhino3dm.Transform.Translation(end.X, end.Y, end.Z))
            placed.append(mm)


        placements.append(
            PendantPlacement(
                pendant=config.pendants[i],
                start=sp,
                end=end,
                meshes=tuple(placed),
            )
        )

    return placements


# -------------------------------------------------------------#
# CABLES
# -------------------------------------------------------------#

def build_cables_from_placements(
    placements: Iterable[PendantPlacement],
):
    meshes: List[rhino3dm.Mesh] = []
    ends: List[rhino3dm.Point3d] = []

    for pl in placements:
        sp, ep = pl.start, pl.end
        d = rhino3dm.Vector3d(ep.X - sp.X, ep.Y - sp.Y, ep.Z - sp.Z)
        length = d.Length()
        if length < 1e-6:
            continue

        cyl = create_cylinder_mesh(CABLE_RADIUS_MM, length, 32)
        cyl.Transform(_rotation_from_z(d))
        cyl.Transform(rhino3dm.Transform.Translation(sp.X, sp.Y, sp.Z))
        meshes.append(cyl)
        ends.append(ep)

    return meshes, ends
