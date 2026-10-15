"""Custo médio e resultado (RB-034 a RB-036): exemplos de manual e propriedades."""

import random
from datetime import date
from decimal import Decimal

import pytest

from src.features.investments import position

D = Decimal
DAY = date(2026, 1, 10)


def op(kind, quantity="0", price="0", fees="0", amount="0", day=DAY):
    return position.Op(kind, day, D(quantity), D(price), D(fees), D(amount))


def test_buy_accumulates_quantity_and_cost_including_fees():
    p = position.replay([op("buy", "10", "20", "5"), op("buy", "10", "30", "5")])

    assert p.quantity == D("20")
    assert p.cost == D("510.00")  # 205 + 305
    assert p.avg_cost == D("25.500000")
    assert p.invested == D("510.00")
    assert p.first_buy == DAY


def test_partial_sell_uses_average_cost_and_leaves_the_rest():
    p = position.replay([op("buy", "10", "20"), op("sell", "4", "30", "2")])

    assert p.quantity == D("6")
    assert p.cost == D("120.00")  # 200 − 80
    assert p.sells == [(D("80.00"), D("38.00"))]  # produto 118 − custo 80
    assert p.proceeds == D("118.00")
    assert p.realized == D("38.00")


def test_selling_everything_clears_cost_without_rounding_residue():
    p = position.replay([op("buy", "3", "10.01"), op("sell", "1", "11"), op("sell", "2", "11")])

    assert p.quantity == D("0")
    assert p.cost == D("0.00")


def test_loss_is_negative_realized_result():
    p = position.replay([op("buy", "10", "20"), op("sell", "10", "15")])

    assert p.realized == D("-50.00")


def test_income_does_not_change_quantity_or_cost():
    p = position.replay([op("buy", "10", "20"), op("income", amount="7")])

    assert (p.quantity, p.cost, p.income) == (D("10"), D("200.00"), D("7"))


def test_adjust_changes_quantity_but_not_cost():
    p = position.replay([op("buy", "10", "20"), op("adjust", "10")])  # desdobramento 2:1

    assert p.quantity == D("20")
    assert p.cost == D("200.00")
    assert p.avg_cost == D("10.000000")


def test_selling_more_than_owned_is_rejected():
    with pytest.raises(position.PositionError):
        position.replay([op("buy", "5", "10"), op("sell", "6", "10")])


def test_adjust_cannot_make_quantity_negative():
    with pytest.raises(position.PositionError):
        position.replay([op("buy", "5", "10"), op("adjust", "-6")])


@pytest.mark.parametrize("seed", range(30))
def test_cost_and_result_are_consistent_for_random_histories(seed):
    rng = random.Random(seed)
    ops, owned = [], D("0")
    for _ in range(rng.randint(2, 25)):
        if owned > 0 and rng.random() < 0.4:
            quantity = D(rng.randint(1, int(owned)))
            ops.append(op("sell", str(quantity), str(rng.randint(5, 50)), str(rng.randint(0, 5))))
            owned -= quantity
        else:
            quantity = D(rng.randint(1, 100))
            ops.append(op("buy", str(quantity), str(rng.randint(5, 50)), str(rng.randint(0, 5))))
            owned += quantity

    p = position.replay(ops)

    assert p.quantity == owned
    assert p.cost >= 0
    # Tudo que se investiu é custo restante ou custo das vendas; o resultado é produto − custo vendido.
    sold_basis = sum((basis for basis, _ in p.sells), D("0"))
    assert p.invested == p.cost + sold_basis
    assert p.realized == p.proceeds - sold_basis
    assert (p.quantity > 0) or p.cost == D("0.00")
