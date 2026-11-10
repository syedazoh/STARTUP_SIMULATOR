from pathlib import Path

from app.models.demo_dataset import Dataset
from app.services.demo_launch import simulate

ROOT = Path(__file__).resolve().parents[2] / "datasets/product-launch-v1"


def test_launch_rules_are_reproducible_and_inventory_bounded():
    data = Dataset.model_validate_json((ROOT / "dataset.json").read_text())
    result = simulate(data, "campaign-launch", 100000)
    assert result == simulate(data, "campaign-launch", 100000)
    assert result["new_orders"] == result["fulfilled_units"] == 100
    assert result["revenue_minor"] == 525000  # 100 new + 5 pending × $50
    assert result["ending_cash_minor"] == 2375000
    assert result["remaining_inventory"] == 45
    assert result["contribution_minor"] == 215000
    assert result["goal_met"] is True


def test_capacity_and_evaluation_baselines():
    data = Dataset.model_validate_json((ROOT / "dataset.json").read_text())
    data.company.staffed_units_per_day = 1
    result = simulate(data, "campaign-launch", 100000)
    assert result["fulfilled_units"] == 2
    assert result["pending_orders_fulfilled"] == 5
    assert result["unfulfilled_new_orders"] == 98
    assert result["goal_met"] is False
