"""Simulation Mode configuration"""

from typing import Dict, Optional

import math
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .event_generator import EVENT_WEIGHTS


class SimulationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    ticks: Optional[int] = Field(default=None, gt=0, le=1000)
    duration_seconds: Optional[float] = Field(default=None, gt=0, le=3600)
    min_interval: float = Field(default=0.5, ge=0, le=60)
    max_interval: float = Field(default=2.0, ge=0, le=60)
    event_weights: Optional[Dict[str, float]] = None

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.max_interval < self.min_interval:
            raise ValueError("max_interval cannot be below min_interval")
        if self.event_weights is not None:
            if set(self.event_weights) - set(EVENT_WEIGHTS):
                raise ValueError("Unknown simulation event type")
            if any(not math.isfinite(v) or v < 0 for v in self.event_weights.values()):
                raise ValueError("Event weights must be finite and non-negative")
        total = sum(self.resolved_weights().values())
        if not math.isfinite(total) or total <= 0:
            raise ValueError("At least one event weight must be positive")
        return self

    def resolved_weights(self) -> Dict[str, float]:
        if not self.event_weights:
            return dict(EVENT_WEIGHTS)
        # Fall back to the default weight for any event type the caller omitted,
        # so a partial override doesn't silently zero out the others.
        return {**EVENT_WEIGHTS, **self.event_weights}
