"""Run from backend: python -m scripts.evaluate_demo. No database or provider calls."""
import json
from pathlib import Path

from app.models.demo_dataset import Dataset
from app.services.demo_launch import simulate


def evaluate():
    root = Path(__file__).resolve().parents[2] / 'datasets/product-launch-v1'
    original = Dataset.model_validate_json((root/'dataset.json').read_text())
    results = []
    for case in json.loads((root/'evaluation/cases.json').read_text()):
        data = original.model_copy(deep=True)
        data.company.staffed_units_per_day = case['staffed_units_per_day']
        data.inventory[0].quantity = case['inventory_quantity']
        data.campaigns[0].conversion_bps = case['conversion_bps']
        campaign = data.campaigns[0]
        proposed = simulate(data, campaign.id, campaign.budget_minor)
        baseline = simulate(data, campaign.id, campaign.baseline_budget_minor)
        assert proposed['fulfilled_units'] == case['expected_fulfilled'], case['id']
        results.append({'case_id': case['id'], 'proposed': proposed, 'baseline': baseline,
                        'contribution_delta_minor': proposed['contribution_minor'] - baseline['contribution_minor']})
    return {'synthetic': True, 'comparison': 'fixed proposed budget versus fixed smaller-budget baseline; not evidence of LLM superiority', 'cases': results}


if __name__ == '__main__':
    print(json.dumps(evaluate(), indent=2))
