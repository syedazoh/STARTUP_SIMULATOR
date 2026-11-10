import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.demo_dataset import Dataset

SAMPLE = Path(__file__).resolve().parents[2] / "datasets/product-launch-v1/dataset.json"


def test_sample_is_consistent_and_synthetic():
    data = Dataset.model_validate_json(SAMPLE.read_text())
    assert data.synthetic is True
    assert data.company.starting_capital_minor == 2000000
    assert data.campaigns[0].product_id == data.inventory[0].id


@pytest.mark.parametrize(
    "mutation",
    [
        "foreign_product",
        "duplicate",
        "real",
        "currency",
        "money",
        "future",
        "numeric_label",
    ],
)
def test_invalid_records_are_rejected(mutation):
    data = json.loads(SAMPLE.read_text())
    if mutation == "foreign_product":
        data["orders"][0]["product_id"] = "absent"
    elif mutation == "duplicate":
        data["sales"].append(copy.deepcopy(data["sales"][0]))
    elif mutation == "real":
        data["synthetic"] = False
    elif mutation == "currency":
        data["currency"] = "DOLLARS"
    elif mutation == "money":
        data["expenses"][0]["amount_minor"] = -1
    elif mutation == "numeric_label":
        data["synthetic"] = 1
    else:
        data["sales"][0]["date"] = "2099-01-01"
    with pytest.raises(ValidationError):
        Dataset.model_validate(data)
