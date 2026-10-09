"""Exportação CSV do DRE e do fluxo de caixa (RF-037).

Formato pensado para o Excel em português do Brasil: separador `;`, vírgula decimal e
UTF-8 com BOM (sem ele o Excel mostra os acentos quebrados).

SEGURANÇA (11-security.md, "CSV injection"): uma célula de TEXTO que começa com `=`, `+`,
`-`, `@`, tab ou retorno de carro pode ser executada como fórmula quando a planilha é
aberta. Todo texto vindo do usuário (nome de categoria, descrição) passa por `safe_text`.
Números NÃO passam por ele: um valor negativo legítimo começa com `-`.
"""

import csv
import io
from decimal import Decimal

from src.features.reports.balances_dre import Dre
from src.features.reports.cash_flow import CashFlow

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
BOM = "﻿"


def safe_text(value: str | None) -> str:
    """Neutraliza fórmula prefixando apóstrofo (o Excel mostra o texto e esconde o apóstrofo)."""
    text = value or ""
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return text


def number(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}".replace(".", ",")


def _write(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, delimiter=";", lineterminator="\r\n").writerows(rows)
    return BOM + buffer.getvalue()


def dre_csv(dre: Dre) -> str:
    rows: list[list[str]] = [
        [safe_text(f"DRE de {dre.start_date:%d/%m/%Y} a {dre.end_date:%d/%m/%Y}")]
        + ([safe_text("(inclui previsto)")] if dre.include_forecast else []),
        [
            "Linha", "Categoria", "Valor", "% da receita líquida",
            f"Anterior ({dre.previous_start_date:%d/%m/%Y} a {dre.previous_end_date:%d/%m/%Y})",
        ],
    ]
    for line in dre.lines:
        rows.append(
            [
                safe_text(line.label),
                "",
                number(line.amount),
                number(line.percent_of_net_revenue),
                number(line.previous_amount),
            ]
        )
        # A categoria vai em coluna própria: o nome é a célula inteira, então safe_text vale.
        # (Indentar com espaços antes de sanitizar deixaria `   =FÓRMULA` passar.)
        for category in line.categories:
            rows.append(["", safe_text(category.name), number(category.amount), "", ""])
    return _write(rows)


def cash_flow_csv(flow: CashFlow) -> str:
    rows: list[list[str]] = [
        [
            "Mês", "Situação", "Saldo inicial", "Entradas previstas", "Saídas previstas",
            "Entradas realizadas", "Saídas realizadas", "Entradas projetadas", "Saídas projetadas",
            "Saldo final projetado", "Saldo final realizado",
        ]
    ]
    status_labels = {"past": "passado", "current": "atual", "future": "futuro"}
    for month in flow.months:
        rows.append(
            [
                month.month,
                status_labels[month.status],
                number(month.opening_balance),
                number(month.planned_in),
                number(month.planned_out),
                number(month.realized_in),
                number(month.realized_out),
                number(month.projected_in),
                number(month.projected_out),
                number(month.closing_projected),
                number(month.closing_realized),
            ]
        )
    return _write(rows)
