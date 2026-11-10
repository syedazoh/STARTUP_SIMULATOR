"""Bounded, synthetic-only snapshot. Money is integer USD cents, never floats."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ID = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
Text = Annotated[str, Field(min_length=1, max_length=500)]
Money = Annotated[int, Field(strict=True, ge=0, le=10**12)]
Count = Annotated[int, Field(strict=True, ge=0, le=1000000)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: ID


class Company(Record):
    name: Text
    starting_capital_minor: Money
    staffed_units_per_day: Count


class Goal(Record):
    description: Text
    due_date: date
    target_units: Count


class Inventory(Record):
    name: Text
    quantity: Count
    unit_price_minor: Annotated[int, Field(strict=True, gt=0, le=10**12)]
    unit_cost_minor: Money


class Order(Record):
    date: date
    product_id: ID
    quantity: Annotated[int, Field(strict=True, gt=0, le=1000000)]
    status: Literal["pending", "fulfilled"]


class Sale(Record):
    date: date
    order_id: ID
    amount_minor: Money


class Expense(Record):
    date: date
    category: Text
    amount_minor: Money


class Campaign(Record):
    name: Text
    product_id: ID
    goal_id: ID
    launch_date: date
    duration_days: Annotated[int, Field(strict=True, ge=1, le=365)]
    budget_minor: Annotated[int, Field(strict=True, gt=0, le=10**12)]
    baseline_budget_minor: Money
    reach_per_100_minor: Count
    conversion_bps: Annotated[int, Field(strict=True, ge=0, le=10000)]


class Candidate(Record):
    name: Text
    role: Text
    skills: list[Text] = Field(max_length=20)
    available_from: date
    status: Literal["applied", "shortlisted", "declined"]


class Reference(Record):
    title: Text
    version: Annotated[int, Field(strict=True, ge=1)]
    department: Literal["all", "finance", "marketing", "hr", "operations", "ceo"]
    text: Annotated[str, Field(min_length=1, max_length=10000)]


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal[1]
    dataset_id: ID
    synthetic: Literal[True]
    currency: Literal["USD"]
    as_of: date
    company: Company
    goals: list[Goal] = Field(min_length=1, max_length=50)
    inventory: list[Inventory] = Field(min_length=1, max_length=100)
    orders: list[Order] = Field(max_length=100)
    sales: list[Sale] = Field(max_length=100)
    expenses: list[Expense] = Field(max_length=100)
    campaigns: list[Campaign] = Field(min_length=1, max_length=20)
    candidates: list[Candidate] = Field(max_length=100)
    references: list[Reference] = Field(max_length=30)

    @field_validator("synthetic", mode="before")
    @classmethod
    def explicit_synthetic_label(cls, value):
        if value is not True:
            raise ValueError("synthetic must be the boolean true")
        return value

    @model_validator(mode="after")
    def relationships(self):
        rows = [self.company] + [r for name in TABLES for r in getattr(self, name)]
        ids = [r.id for r in rows]
        if len(ids) != len(set(ids)):
            raise ValueError("Record IDs must be unique across the snapshot")
        products = {r.id: r for r in self.inventory}
        orders = {r.id: r for r in self.orders}
        goals = {r.id for r in self.goals}
        for order in self.orders:
            if order.product_id not in products:
                raise ValueError(f"orders/{order.id}/product_id: unknown product")
        sold = set()
        for sale in self.sales:
            order = orders.get(sale.order_id)
            if not order or order.status != "fulfilled" or sale.order_id in sold:
                raise ValueError(
                    f"sales/{sale.id}/order_id: requires unique fulfilled order"
                )
            if (
                sale.amount_minor
                != order.quantity * products[order.product_id].unit_price_minor
            ):
                raise ValueError(
                    f"sales/{sale.id}/amount_minor: must equal order quantity × price"
                )
            sold.add(sale.order_id)
        if sold != {o.id for o in self.orders if o.status == "fulfilled"}:
            raise ValueError("Each fulfilled order requires exactly one sale")
        for row in self.sales + self.expenses + self.orders:
            if row.date > self.as_of:
                raise ValueError(f"{row.id}/date: historical record is after as_of")
        for campaign in self.campaigns:
            if campaign.product_id not in products or campaign.goal_id not in goals:
                raise ValueError(f"campaigns/{campaign.id}: unknown product or goal")
            if campaign.launch_date < self.as_of:
                raise ValueError("Campaign launch must be on or after as_of")
        return self


TABLES = (
    "goals",
    "inventory",
    "orders",
    "sales",
    "expenses",
    "campaigns",
    "candidates",
    "references",
)
