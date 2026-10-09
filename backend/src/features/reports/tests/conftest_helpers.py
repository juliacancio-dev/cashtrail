"""Helpers compartilhados pelos testes de reports (montagem de cenário via API)."""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

# "Hoje" fixo e no passado: as regras da API que olham o relógio real (data de pagamento
# não pode ser futura) continuam válidas, e os relatórios ficam determinísticos.
TODAY = date(2026, 8, 20)
D = Decimal


@dataclass
class World:
    client: object
    headers: dict
    user_id: uuid.UUID
    checking: str
    savings: str
    card_account: str
    card_id: str
    salary: str      # grupo revenue
    rent: str        # grupo fixed_expense
    market: str      # grupo variable_expense
    ungrouped: str   # sem grupo

    def post(self, path: str, **body):
        response = self.client.post(path, json=body, headers=self.headers)
        assert response.status_code in (200, 201, 204), f"{path}: {response.status_code} {response.text}"
        return response.json() if response.content else None

    def tx(self, account: str, category: str, kind: str, amount: str, day: str, description: str | None = None):
        return self.post(
            "/transactions",
            account_id=account, category_id=category, type=kind, amount=amount, occurred_at=day,
            description=description,
        )

    def get(self, path: str, **params):
        response = self.client.get(path, params=params, headers=self.headers)
        assert response.status_code == 200, f"{path}: {response.status_code} {response.text}"
        return response

    def month(self, flow, key: str):
        return next(m for m in flow.months if m.month == key)


def make_world(client, email: str, checking_opening: str = "1000.00", savings_opening: str = "500.00") -> World:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json=payload).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    def create(path: str, body: dict) -> str:
        response = client.post(path, json=body, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()["id"]

    checking = create("/accounts", {"name": "Corrente", "type": "checking", "opening_balance": checking_opening})
    savings = create("/accounts", {"name": "Poupança", "type": "savings", "opening_balance": savings_opening})
    card_account = create("/accounts", {"name": "Cartão", "type": "credit_card"})
    card_id = create(
        "/cards",
        {"account_id": card_account, "closing_day": 5, "due_day": 12, "default_payment_account_id": checking},
    )
    return World(
        client=client,
        headers=headers,
        user_id=uuid.UUID(client.get("/auth/me", headers=headers).json()["id"]),
        checking=checking,
        savings=savings,
        card_account=card_account,
        card_id=card_id,
        salary=create("/categories", {"name": "Salário", "dre_group": "revenue"}),
        rent=create("/categories", {"name": "Aluguel", "dre_group": "fixed_expense"}),
        market=create("/categories", {"name": "Mercado", "dre_group": "variable_expense"}),
        ungrouped=create("/categories", {"name": "Diversos"}),
    )
