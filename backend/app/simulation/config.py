"""Simulation Mode configuration"""
from typing import Dict, Optional

from pydantic import BaseModel, Field, model_validator

from .event_generator import EVENT_WEIGHTS

# Server-owned work budget; applies even when callers omit a run limit.
MAX_SIMULATION_TICKS = 1000
MIN_SIMULATION_INTERVAL = 0.1


class SimulationConfig(BaseModel):
    ticks: Optional[int] = Field(
        default=None, ge=1, le=MAX_SIMULATION_TICKS,
        description="Maximum ticks; omitted or null uses the server limit of 1000.",
    )
    duration_seconds: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    min_interval: float = Field(default=0.5, ge=MIN_SIMULATION_INTERVAL, allow_inf_nan=False)
    max_interval: float = Field(default=2.0, ge=MIN_SIMULATION_INTERVAL, allow_inf_nan=False)
    event_weights: Optional[Dict[str, float]] = None

    @model_validator(mode="after")
    def validate_intervals(self) -> "SimulationConfig":
        if self.max_interval < self.min_interval:
            raise ValueError("max_interval must be at least min_interval")
        return self

    def resolved_weights(self) -> Dict[str, float]:
        if not self.event_weights:
            return dict(EVENT_WEIGHTS)
        # Fall back to the default weight for any event type the caller omitted,
        # so a partial override doesn't silently zero out the others.
        return {**EVENT_WEIGHTS, **self.event_weights}
