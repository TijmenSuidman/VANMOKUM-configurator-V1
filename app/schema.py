from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ClusterType(str, Enum):
    """Spatial distribution pattern for a round canopy."""

    RING = "ring"
    RING_WITH_CENTER = "ring_with_center"
    RANDOM_RING = "random_ring"


CanopySize = Literal["s", "m", "l"]

CanopyAppearance = Literal["canopy_black", "canopy_white"]
CableAppearance = Literal["cable_black", "cable_white"]
ShadeAppearance = Literal["shade_white", "shade_blonde", "shade_natural"]


class CanopyConfig(BaseModel):
    size: CanopySize = Field(..., description="Canopy size key.")
    appearance: CanopyAppearance = Field(..., description="Material preset key for canopy.")


class CableConfig(BaseModel):
    appearance: CableAppearance = Field("cable_black", description="Material preset key for cables.")


class LayoutConfig(BaseModel):
    cluster_type: Optional[ClusterType] = Field(
        None, description="Layout type. If omitted, a default is applied."
    )
    first_drop_mm: int = Field(1400, ge=100, le=6000)
    total_drop_mm: int = Field(2000, ge=200, le=8000)

    @model_validator(mode="after")
    def _validate_drops(self):
        if self.total_drop_mm < self.first_drop_mm:
            raise ValueError("layout.total_drop_mm must be >= layout.first_drop_mm")
        return self


class PendantConfig(BaseModel):
    model: str = Field(..., description="Pendant model key.")
    appearance: ShadeAppearance = Field("shade_natural", description="Material preset key for shade.")


class ClusterConfig(BaseModel):
    canopy: CanopyConfig
    cable: CableConfig = Field(default_factory=CableConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    pendants: List[PendantConfig]

    random_seed: int = Field(0, ge=0, le=2_147_483_647)
    defaults_applied: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _apply_defaults(self):
        if self.layout.cluster_type is None:
            # v3 behavior: ring for <=3, ring with center for >3
            n = len(self.pendants)
            self.layout.cluster_type = (
                ClusterType.RING if n <= 3 else ClusterType.RING_WITH_CENTER
            )
            self.defaults_applied.append("layout.cluster_type defaulted")
        return self

    @property
    def num_pendants(self) -> int:
        return len(self.pendants)
