"""Parâmetros fiscais por ano-calendário (RB-042, decisão 3): dados versionados, não lógica.

Cada arquivo `parameters/<ano>.json` traz os valores, as fontes oficiais consultadas, a data da consulta
e a lista do que NÃO foi verificado. Pedir um ano sem arquivo é erro explícito (nunca usa o ano vizinho).
"""

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

PARAMETERS_DIR = Path(__file__).parent / "parameters"


class UnsupportedYearError(Exception):
    """Não há parâmetros fiscais para o ano pedido."""


@dataclass(frozen=True)
class Band:
    up_to: Decimal | None  # None = sem teto
    rate: Decimal
    deduction: Decimal


@dataclass(frozen=True)
class Reducer:
    full_up_to: Decimal
    full_amount: Decimal
    phase_out_up_to: Decimal
    phase_constant: Decimal
    phase_factor: Decimal


@dataclass(frozen=True)
class VariableIncome:
    stock_exempt_monthly_sales: Decimal
    stock_rate: Decimal
    fii_rate: Decimal
    irrf_rate: Decimal
    darf_code: str
    darf_minimum: Decimal


@dataclass(frozen=True)
class TaxParameters:
    year: int
    label: str
    consulted_at: date
    sources: list[dict]
    annual_table: list[Band]
    dependent_deduction: Decimal
    education_limit_per_person: Decimal
    simplified_limit: Decimal
    simplified_rate: Decimal
    pension_limit_rate: Decimal
    reducer: Reducer
    variable_income: VariableIncome
    unverified: list[str]


def _d(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def load(year: int) -> TaxParameters:
    path = PARAMETERS_DIR / f"{year}.json"
    if not path.is_file():
        raise UnsupportedYearError(year)
    raw = json.loads(path.read_text(encoding="utf-8"))
    reducer = raw["reducer"]
    variable = raw["variable_income"]
    return TaxParameters(
        year=int(raw["year"]),
        label=raw["label"],
        consulted_at=date.fromisoformat(raw["consulted_at"]),
        sources=raw["sources"],
        annual_table=[Band(_d(b["up_to"]), Decimal(b["rate"]), Decimal(b["deduction"])) for b in raw["annual_table"]],
        dependent_deduction=Decimal(raw["dependent_deduction"]),
        education_limit_per_person=Decimal(raw["education_limit_per_person"]),
        simplified_limit=Decimal(raw["simplified_limit"]),
        simplified_rate=Decimal(raw["simplified_rate"]),
        pension_limit_rate=Decimal(raw["pension_limit_rate"]),
        reducer=Reducer(
            full_up_to=Decimal(reducer["full_up_to"]),
            full_amount=Decimal(reducer["full_amount"]),
            phase_out_up_to=Decimal(reducer["phase_out_up_to"]),
            phase_constant=Decimal(reducer["phase_constant"]),
            phase_factor=Decimal(reducer["phase_factor"]),
        ),
        variable_income=VariableIncome(
            stock_exempt_monthly_sales=Decimal(variable["stock_exempt_monthly_sales"]),
            stock_rate=Decimal(variable["stock_rate"]),
            fii_rate=Decimal(variable["fii_rate"]),
            irrf_rate=Decimal(variable["irrf_rate"]),
            darf_code=variable["darf_code"],
            darf_minimum=Decimal(variable["darf_minimum"]),
        ),
        unverified=list(raw.get("unverified", [])),
    )


def available_years() -> list[int]:
    return sorted(int(p.stem) for p in PARAMETERS_DIR.glob("*.json") if p.stem.isdigit())
