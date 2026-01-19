from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.cache import glb_exists, glb_path_for_hash, hash_config
from app.codec import decode_code_to_config
from app.settings import GLB_OUTPUT_DIR
from app.builder.build import build_mesh_groups
from app.builder.exporter import save_mesh_groups_as_glb


router = APIRouter()


class GenerateRequest(BaseModel):
    code: str


@router.post("/generate_from_code")
def generate_from_code(payload: GenerateRequest, request: Request):
    try:
        config = decode_code_to_config(payload.code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    hash_value = hash_config(config)
    out_path = glb_path_for_hash(hash_value, GLB_OUTPUT_DIR)

    if not glb_exists(hash_value, GLB_OUTPUT_DIR):
        mesh_groups, material_keys = build_mesh_groups(config)
        try:
            save_mesh_groups_as_glb(mesh_groups, material_keys, str(out_path))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"GLB export failed: {exc}")

    # Return a relative URL so WordPress / reverse proxies can rewrite host cleanly.
    return {"glb_url": f"/glb/{hash_value}.glb", "hash": hash_value}
