"""Regression tests for the bounds applied to a CEO arbitration ruling's
final_amount before it moves money.

The ruling is model output, and its subscribers subtract it straight from
Finance's budget_pool (and grow Marketing's customer_base off it), so the amount
has to be bounded at both ends: CEOAgent._clamp_arbitration_amount clamps it to
what Marketing actually asked for before publishing, and
FinanceAgent.handle_arbitration_result / MarketingAgent.handle_arbitration_result
re-validate independently rather than trusting the event payload.
"""
import math

import pytest

from app.agents.ceo_agent import CEOAgent
from app.agents.schemas import ArbitrationDecision


def _ruling(final_amount, winner="compromise"):
    return ArbitrationDecision(
        winner=winner, final_amount=final_amount, rationale="synthetic ruling for test"
    )


def _marketing_position(requested_amount):
    return {"requested_amount": requested_amount, "campaign_name": "Test Campaign", "department": "Marketing"}


@pytest.mark.parametrize(
    "model_amount,expected",
    [
        (50_000.0, 50_000.0),  # in range and under the request — untouched
        (200_000.0, 200_000.0),  # exactly the requested amount — allowed
        (500_000.0, 200_000.0),  # over the request — clamped down
        (-5_000.0, 0.0),  # negative — clamped to a zero release
        (0.0, 0.0),  # zero stays zero
    ],
)
def test_clamp_bounds_the_ruling_to_the_requested_amount(model_amount, expected):
    ceo = CEOAgent()
    decision = CEOAgent._clamp_arbitration_amount(ceo, _ruling(model_amount), _marketing_position(200_000.0))

    assert decision.final_amount == expected
    assert math.isfinite(decision.final_amount)
    assert decision.final_amount >= 0


@pytest.mark.parametrize("winner", ["marketing", "compromise"])
def test_non_finite_amounts_are_zeroed_rather_than_applied(winner):
    ceo = CEOAgent()
    decision = CEOAgent._clamp_arbitration_amount(
        ceo, _ruling(float("inf"), winner=winner), _marketing_position(100_000.0)
    )
    assert decision.final_amount == 0.0

    decision = CEOAgent._clamp_arbitration_amount(
        ceo, _ruling(float("nan"), winner=winner), _marketing_position(100_000.0)
    )
    assert decision.final_amount == 0.0


def test_finance_winning_zeroes_the_amount_even_if_the_model_returns_one():
    ceo = CEOAgent()
    decision = CEOAgent._clamp_arbitration_amount(
        ceo, _ruling(75_000.0, winner="finance"), _marketing_position(200_000.0)
    )
    assert decision.final_amount == 0.0


def test_non_numeric_requested_amount_treated_as_zero():
    ceo = CEOAgent()
    decision = CEOAgent._clamp_arbitration_amount(
        ceo, _ruling(50_000.0), {"requested_amount": "not-a-number"}
    )
    assert decision.final_amount == 0.0


def test_an_adjusted_ruling_is_annotated_so_the_change_is_auditable():
    ceo = CEOAgent()
    decision = CEOAgent._clamp_arbitration_amount(
        ceo, _ruling(999_999.0), _marketing_position(200_000.0)
    )
    assert "ADJUSTED" in decision.rationale


@pytest.mark.asyncio
class TestFinanceConsumerReValidates:
    async def test_finance_never_subtracts_more_than_the_pool(self):
        from app.agents.finance_agent import FinanceAgent

        finance = FinanceAgent(budget_pool=10_000.0)
        result = await finance.handle_arbitration_result({"winner": "marketing", "final_amount": 5_000_000.0})

        assert result["final_amount"] == 10_000.0
        assert finance.budget_pool == 0.0

    @pytest.mark.parametrize("final_amount", [-1_000.0, float("nan"), float("inf"), "abc", None])
    async def test_finance_ignores_non_positive_and_non_numeric_amounts(self, final_amount):
        from app.agents.finance_agent import FinanceAgent

        finance = FinanceAgent(budget_pool=10_000.0)
        result = await finance.handle_arbitration_result(
            {"winner": "marketing", "final_amount": final_amount}
        )

        assert result["final_amount"] == 0.0
        assert finance.budget_pool == 10_000.0

    async def test_finance_financial_win_releases_nothing(self):
        from app.agents.finance_agent import FinanceAgent

        finance = FinanceAgent(budget_pool=10_000.0)
        await finance.handle_arbitration_result({"winner": "finance", "final_amount": 4_000.0})
        assert finance.budget_pool == 10_000.0

    async def test_marketing_does_not_grow_on_a_negative_amount(self):
        from app.agents.marketing_agent import MarketingAgent

        marketing = MarketingAgent()
        starting_customers = marketing.customer_base
        starting_brand = marketing.brand_value

        await marketing.handle_arbitration_result({"winner": "marketing", "final_amount": -50_000.0})

        assert marketing.customer_base == starting_customers
        assert marketing.brand_value == starting_brand