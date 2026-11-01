"""Synthetic event generator for Simulation Mode"""

import random
import math
from typing import Any, Dict, Optional, Tuple

EVENT_WEIGHTS = {
    "campaign_launch": 0.35,
    "budget_request": 0.25,
    "recruitment_request": 0.20,
    "resource_request": 0.20,
}

CAMPAIGN_NAMES = [
    "Spring Sale",
    "Referral Push",
    "Brand Awareness Blitz",
    "Product Launch Hype",
    "Holiday Promo",
    "Influencer Partnership",
    "Retargeting Sprint",
    "Loyalty Rewards",
]

# Below this brand_value, campaigns get weighted up — a low-brand-value business
# should be more likely to try to fix it.
LOW_BRAND_VALUE_THRESHOLD = 80
# Above this employees-per-resource-unit ratio, hiring slows and resourcing speeds
# up — headcount is outgrowing the infrastructure to support it.
HIGH_HEADCOUNT_RATIO_THRESHOLD = 0.01


def _apply_state_adjustments(
    weights: Dict[str, float], agent_statuses: Dict[str, Dict[str, Any]]
) -> Dict[str, float]:
    adjusted = dict(weights)

    marketing = agent_statuses.get("marketing", {})
    brand_value = marketing.get("brand_value")
    if brand_value is not None and brand_value < LOW_BRAND_VALUE_THRESHOLD:
        adjusted["campaign_launch"] = adjusted.get("campaign_launch", 0) * 1.6

    hr = agent_statuses.get("hr", {})
    operations = agent_statuses.get("operations", {})
    employee_count = hr.get("employee_count")
    resource_pool = operations.get("resource_pool")
    if employee_count is not None and resource_pool:
        ratio = employee_count / max(resource_pool, 1)
        if ratio > HIGH_HEADCOUNT_RATIO_THRESHOLD:
            adjusted["recruitment_request"] = (
                adjusted.get("recruitment_request", 0) * 0.7
            )
            adjusted["resource_request"] = adjusted.get("resource_request", 0) * 1.5

    return adjusted


def generate_event(
    weights: Optional[Dict[str, float]] = None,
    agent_statuses: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Pick a random event type and a randomized payload for it.

    `weights` overrides the default event-type mix; `agent_statuses` (as returned
    by AgentManager.get_all_agents_status()) nudges those weights based on current
    business state, e.g. more campaigns when brand value is sagging.
    """
    resolved = dict(weights) if weights else dict(EVENT_WEIGHTS)
    if (
        set(resolved) - set(EVENT_WEIGHTS)
        or any(not math.isfinite(v) or v < 0 for v in resolved.values())
        or not math.isfinite(sum(resolved.values()))
        or sum(resolved.values()) <= 0
    ):
        raise ValueError(
            "Simulation weights must use supported events with a positive finite total"
        )
    total = sum(resolved.values())
    resolved = {kind: weight / total for kind, weight in resolved.items()}
    if agent_statuses:
        resolved = _apply_state_adjustments(resolved, agent_statuses)

    event_type = random.choices(
        list(resolved.keys()), weights=list(resolved.values()), k=1
    )[0]

    if event_type == "campaign_launch":
        return event_type, {
            "campaign_name": random.choice(CAMPAIGN_NAMES),
            "requested_budget": round(random.uniform(1000, 60000), 2),
        }
    if event_type == "budget_request":
        return event_type, {
            "department": random.choice(["Operations", "HR", "General"]),
            "amount": round(random.uniform(500, 20000), 2),
        }
    if event_type == "recruitment_request":
        return event_type, {
            "role": random.choice(
                ["Engineer", "Sales Rep", "Designer", "Support Agent"]
            ),
            "headcount": random.randint(1, 5),
        }
    return event_type, {
        "resource_type": random.choice(["Cloud Compute", "Office Space", "Equipment"]),
        "quantity": random.randint(1, 10),
    }
