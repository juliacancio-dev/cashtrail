"""Posição de um ativo a partir das operações (RB-034 a RB-036). Funções puras, sem banco.

Custo médio por média ponderada móvel. Corretagem e taxas da compra integram o custo; as da venda
reduzem o produto (e portanto o ganho).
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


class PositionError(Exception):
    """Operação impossível: vender mais do que se tem, ou ajuste que deixa a quantidade negativa."""


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Op:
    kind: str  # buy | sell | income | adjust
    occurred_at: date
    quantity: Decimal = Decimal("0")
    unit_price: Decimal = Decimal("0")
    fees: Decimal = ZERO
    amount: Decimal = ZERO  # provento: valor recebido


@dataclass
class Position:
    quantity: Decimal = Decimal("0")
    cost: Decimal = ZERO  # custo da quantidade que ainda se tem
    invested: Decimal = ZERO  # soma do custo de todas as compras
    proceeds: Decimal = ZERO  # soma do produto líquido de todas as vendas
    income: Decimal = ZERO  # proventos recebidos
    realized: Decimal = ZERO  # ganho/perda realizado nas vendas
    first_buy: date | None = None
    sells: list[tuple[Decimal, Decimal]] = field(default_factory=list)  # (cost_basis, gain) por venda

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity <= 0:
            return ZERO
        return (self.cost / self.quantity).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def buy_cost(quantity: Decimal, unit_price: Decimal, fees: Decimal) -> Decimal:
    return money(quantity * unit_price + fees)


def sell_proceeds(quantity: Decimal, unit_price: Decimal, fees: Decimal) -> Decimal:
    return money(quantity * unit_price - fees)


def apply(position: Position, op: Op) -> tuple[Decimal | None, Decimal | None]:
    """Aplica uma operação e devolve (cost_basis, gain) quando é venda."""
    if op.kind == "buy":
        cost = buy_cost(op.quantity, op.unit_price, op.fees)
        position.quantity += op.quantity
        position.cost += cost
        position.invested += cost
        if position.first_buy is None:
            position.first_buy = op.occurred_at
        return None, None

    if op.kind == "sell":
        if op.quantity <= 0 or op.quantity > position.quantity:
            raise PositionError("venda acima da quantidade em carteira")
        if op.quantity == position.quantity:
            basis = position.cost  # zera sem resíduo de arredondamento
        else:
            basis = money(position.cost * op.quantity / position.quantity)
        proceeds = sell_proceeds(op.quantity, op.unit_price, op.fees)
        gain = proceeds - basis
        position.quantity -= op.quantity
        position.cost -= basis
        position.proceeds += proceeds
        position.realized += gain
        position.sells.append((basis, gain))
        return basis, gain

    if op.kind == "income":
        position.income += op.amount
        return None, None

    if op.kind == "adjust":
        if position.quantity + op.quantity < 0:
            raise PositionError("o ajuste deixaria a quantidade negativa")
        position.quantity += op.quantity
        return None, None

    raise PositionError(f"tipo de operacao invalido: {op.kind}")


def replay(ops: list[Op]) -> Position:
    """Operações em ordem cronológica (a ordem da lista é a do desempate no mesmo dia)."""
    position = Position()
    for op in ops:
        apply(position, op)
    return position
