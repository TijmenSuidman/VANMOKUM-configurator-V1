import json
import struct
import math
import rhino3dm

from app.builder.materials import get_material_preset


def pad_to_4(data: bytes) -> bytes:
    while len(data) % 4 != 0:
        data += b"\x00"
    return data


def pad_json_to_4(json_str: str) -> bytes:
    data = json_str.encode("utf-8")
    while len(data) % 4 != 0:
        data += b" "
    return data


def mapping_type_from_material_key(key: str) -> str:
    return "cylindrical" if key.startswith("shade_") else "planar"


def compute_planar_uv(x, y, scale=500.0):
    return (x / scale) + 0.5, (y / scale) + 0.5


def compute_cylindrical_uv(x, y, z, scale_height=500.0):
    angle = math.atan2(y, x)
    u = (angle / (2 * math.pi)) + 0.5
    v = (z / scale_height) + 0.5
    return u, v


def mesh_to_arrays(mesh: rhino3dm.Mesh, mapping_type="planar"):
    positions = []
    uvs = []
    indices = []

    for v in mesh.Vertices:
        positions.extend([
            v.X / 1000.0,
            v.Z / 1000.0,
            v.Y / 1000.0,
        ])

        if mapping_type == "cylindrical":
            u, vv = compute_cylindrical_uv(v.X, v.Y, v.Z)
        else:
            u, vv = compute_planar_uv(v.X, v.Y)

        uvs.extend([u, vv])

    for f in mesh.Faces:
        if hasattr(f, "IsTriangle"):
            if f.IsTriangle:
                indices.extend([f.A, f.B, f.C])
            else:
                indices.extend([f.A, f.B, f.C, f.A, f.C, f.D])
        else:
            if len(f) == 3:
                indices.extend(f)
            elif len(f) == 4:
                a, b, c, d = f
                indices.extend([a, b, c, a, c, d])

    return positions, uvs, indices


def save_mesh_groups_as_glb(mesh_groups, material_keys, output_path: str):

    buffers = []
    buffer_views = []
    accessors = []
    meshes_out = []
    nodes = []
    materials = []

    material_index_map = {}

    # Materials: pure PBR, no textures
    for key in material_keys:
        preset = get_material_preset(key)
        mat_def = {
            "name": preset["name"],
            "pbrMetallicRoughness": preset["pbrMetallicRoughness"],
            "doubleSided": True,
        }

        material_index_map[key] = len(materials)
        materials.append(mat_def)

    # Meshes
    for mg in mesh_groups:
        mesh = mg["mesh"]
        mat_index = material_index_map[mg["material_key"]]

        positions, uvs, indices = mesh_to_arrays(
            mesh,
            mapping_type_from_material_key(mg["material_key"])
        )

        if not indices:
            continue

        pos = pad_to_4(struct.pack("<" + "f" * len(positions), *positions))
        uv = pad_to_4(struct.pack("<" + "f" * len(uvs), *uvs))
        idx = pad_to_4(struct.pack("<" + "I" * len(indices), *indices))

        pos_off = sum(len(b) for b in buffers)
        buffers.append(pos)

        uv_off = sum(len(b) for b in buffers)
        buffers.append(uv)

        idx_off = sum(len(b) for b in buffers)
        buffers.append(idx)

        bv_pos = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": pos_off, "byteLength": len(pos), "target": 34962})
        bv_uv = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": uv_off, "byteLength": len(uv), "target": 34962})
        bv_idx = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": idx_off, "byteLength": len(idx), "target": 34963})

        acc_pos = len(accessors)
        accessors.append({"bufferView": bv_pos, "componentType": 5126, "count": len(positions)//3, "type": "VEC3"})
        acc_uv = len(accessors)
        accessors.append({"bufferView": bv_uv, "componentType": 5126, "count": len(uvs)//2, "type": "VEC2"})
        acc_idx = len(accessors)
        accessors.append({"bufferView": bv_idx, "componentType": 5125, "count": len(indices), "type": "SCALAR"})

        meshes_out.append({
            "primitives": [{
                "attributes": {"POSITION": acc_pos, "TEXCOORD_0": acc_uv},
                "indices": acc_idx,
                "material": mat_index,
            }]
        })

        nodes.append({"mesh": len(meshes_out) - 1})

    gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes_out,
        "buffers": [{"byteLength": sum(len(b) for b in buffers)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
        "materials": materials,
    }

    json_chunk = pad_json_to_4(json.dumps(gltf))
    bin_chunk = pad_to_4(b"".join(buffers))

    header = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(json_chunk) + 8 + len(bin_chunk))

    with open(output_path, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I4s", len(json_chunk), b"JSON"))
        f.write(json_chunk)
        f.write(struct.pack("<I4s", len(bin_chunk), b"BIN\x00"))
        f.write(bin_chunk)
