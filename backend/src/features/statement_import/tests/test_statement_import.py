"""RF-011/RF-012 (Fluxo 6): pré-visualização, detecção de duplicatas e confirmação."""

import json

CSV = (
    "Data;Descrição;Valor\n"
    "10/09/2026;PADARIA CENTRAL;-12,50\n"
    "11/09/2026;SALARIO EMPRESA;5.000,00\n"
    "12/09/2026;MERCADO BAIRRO;-80,00\n"
).encode("utf-8")


def _register_and_login(client, email: str) -> dict[str, str]:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json=payload).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_account(client, headers, name: str = "Conta Corrente") -> str:
    return client.post("/accounts", json={"name": name, "type": "checking"}, headers=headers).json()["id"]


def _create_category(client, headers, name: str = "Geral") -> str:
    return client.post("/categories", json={"name": name}, headers=headers).json()["id"]


def _preview(client, headers, account_id, content: bytes = CSV, filename: str = "extrato.csv", mapping=None):
    data = {"account_id": account_id}
    if mapping is not None:
        data["mapping"] = json.dumps(mapping)
    return client.post(
        "/statement-imports/preview", headers=headers, data=data, files={"file": (filename, content, "text/csv")}
    )


def _confirm_body(account_id, category_id, preview_body, only=None) -> dict:
    rows = [r for r in preview_body["rows"] if r["error"] is None]
    if only is not None:
        rows = [r for r in rows if r["row_number"] in only]
    return {
        "account_id": account_id,
        "file_name": preview_body["file_name"],
        "file_sha256": preview_body["file_sha256"],
        "rows_total": len(preview_body["rows"]),
        "rows": [
            {
                "occurred_at": r["occurred_at"],
                "type": r["type"],
                "amount": r["amount"],
                "description": r["description"],
                "category_id": category_id,
            }
            for r in rows
        ],
    }


def _transactions(client, headers) -> list[dict]:
    return client.get("/transactions", headers=headers).json()


def test_preview_returns_rows_without_creating_anything(client):
    headers = _register_and_login(client, "imp1@example.com")
    account_id = _create_account(client, headers)

    response = _preview(client, headers, account_id)

    assert response.status_code == 200
    body = response.json()
    assert [(r["type"], r["amount"]) for r in body["rows"]] == [
        ("expense", "12.50"), ("income", "5000.00"), ("expense", "80.00")
    ]
    assert body["mapping"]["date_format"] == "%d/%m/%Y"
    assert body["previously_imported_at"] is None
    assert _transactions(client, headers) == []


def test_confirm_creates_transactions_with_import_source_and_audit_record(client, db_session):
    headers = _register_and_login(client, "imp2@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    body = _preview(client, headers, account_id).json()

    response = client.post(
        "/statement-imports", headers=headers, json=_confirm_body(account_id, category_id, body)
    )

    assert response.status_code == 201
    assert response.json()["transactions_created"] == 3
    assert response.json()["rows_skipped"] == 0
    created = _transactions(client, headers)
    assert len(created) == 3
    assert {t["source"] for t in created} == {"import"}


def test_reimporting_same_file_flags_every_row_as_duplicate(client):
    """Critério de saída do Marco 7 (RF-012): reimportar não duplica em silêncio."""
    headers = _register_and_login(client, "imp3@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    first = _preview(client, headers, account_id).json()
    client.post("/statement-imports", headers=headers, json=_confirm_body(account_id, category_id, first))

    second = _preview(client, headers, account_id).json()

    assert all(row["duplicate_of"] is not None for row in second["rows"])
    assert second["previously_imported_at"] is not None


def test_duplicate_matches_manual_transaction_within_window(client):
    headers = _register_and_login(client, "imp4@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    # Lançamento manual com 1 dia de diferença do extrato (banco compensou em D+1).
    client.post(
        "/transactions",
        headers=headers,
        json={
            "account_id": account_id, "category_id": category_id, "type": "expense",
            "amount": "12.50", "occurred_at": "2026-09-11", "description": "padaria",
        },
    )

    body = _preview(client, headers, account_id).json()

    flagged = [r for r in body["rows"] if r["duplicate_of"]]
    assert [r["row_number"] for r in flagged] == [2]
    assert flagged[0]["duplicate_of"]["description"] == "padaria"


def test_same_amount_outside_window_or_other_type_is_not_duplicate(client):
    headers = _register_and_login(client, "imp5@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    for occurred_at, type_ in [("2026-09-14", "expense"), ("2026-09-10", "income")]:
        client.post(
            "/transactions",
            headers=headers,
            json={
                "account_id": account_id, "category_id": category_id, "type": type_,
                "amount": "12.50", "occurred_at": occurred_at,
            },
        )

    body = _preview(client, headers, account_id).json()

    assert all(r["duplicate_of"] is None for r in body["rows"])


def test_each_existing_transaction_matches_at_most_one_row(client):
    """Duas compras legítimas iguais no mesmo dia, uma já lançada: só uma é duplicata."""
    headers = _register_and_login(client, "imp6@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    client.post(
        "/transactions",
        headers=headers,
        json={
            "account_id": account_id, "category_id": category_id, "type": "expense",
            "amount": "9.90", "occurred_at": "2026-09-10",
        },
    )
    twin_csv = "Data;Descricao;Valor\n10/09/2026;CAFE;-9,90\n10/09/2026;CAFE;-9,90\n".encode()

    body = _preview(client, headers, account_id, twin_csv).json()

    assert [r["duplicate_of"] is not None for r in body["rows"]] == [True, False]


def test_confirm_only_selected_rows_records_skipped_count(client):
    headers = _register_and_login(client, "imp7@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    body = _preview(client, headers, account_id).json()

    response = client.post(
        "/statement-imports", headers=headers, json=_confirm_body(account_id, category_id, body, only={3})
    )

    assert response.json()["transactions_created"] == 1
    assert response.json()["rows_skipped"] == 2
    assert len(_transactions(client, headers)) == 1


def test_confirm_is_all_or_nothing_when_a_category_is_invalid(client):
    headers = _register_and_login(client, "imp8@example.com")
    other = _register_and_login(client, "imp8other@example.com")
    account_id = _create_account(client, headers)
    own_category = _create_category(client, headers)
    foreign_category = _create_category(client, other, "De outro usuario")
    body = _preview(client, headers, account_id).json()
    confirm = _confirm_body(account_id, own_category, body)
    confirm["rows"][2]["category_id"] = foreign_category

    response = client.post("/statement-imports", headers=headers, json=confirm)

    assert response.status_code == 404
    assert _transactions(client, headers) == []


def test_user_cannot_preview_or_import_into_another_users_account(client):
    """RNF-001: isolamento por usuário."""
    owner = _register_and_login(client, "impowner@example.com")
    intruder = _register_and_login(client, "impintruder@example.com")
    account_id = _create_account(client, owner)
    category_id = _create_category(client, intruder)
    body = _preview(client, owner, account_id).json()

    preview = _preview(client, intruder, account_id)
    confirm = client.post(
        "/statement-imports", headers=intruder, json=_confirm_body(account_id, category_id, body)
    )

    assert preview.status_code == 404
    assert confirm.status_code == 404
    assert _transactions(client, owner) == []


def test_archived_account_is_rejected(client):
    headers = _register_and_login(client, "imp9@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    body = _preview(client, headers, account_id).json()
    client.post(f"/accounts/{account_id}/archive", headers=headers)

    preview = _preview(client, headers, account_id)
    confirm = client.post("/statement-imports", headers=headers, json=_confirm_body(account_id, category_id, body))

    assert preview.status_code == 422
    assert confirm.status_code == 422


def test_requires_authentication(client):
    response = client.post(
        "/statement-imports/preview", data={"account_id": "x"}, files={"file": ("a.csv", b"x", "text/csv")}
    )

    assert response.status_code == 401


def test_rejects_non_csv_extension_and_oversized_file(client, monkeypatch):
    headers = _register_and_login(client, "imp10@example.com")
    account_id = _create_account(client, headers)

    wrong_type = _preview(client, headers, account_id, filename="extrato.pdf")
    monkeypatch.setattr("src.features.statement_import.router.MAX_FILE_BYTES", 10)
    too_big = _preview(client, headers, account_id)

    assert wrong_type.status_code == 422
    assert too_big.status_code == 413


def test_unparseable_file_returns_clear_422(client):
    headers = _register_and_login(client, "imp11@example.com")
    account_id = _create_account(client, headers)

    response = _preview(client, headers, account_id, content=b"\x00\x01\x02")

    assert response.status_code == 422
    assert "CSV" in response.json()["detail"]


def test_preview_accepts_user_mapping_and_rejects_invalid_one(client):
    headers = _register_and_login(client, "imp12@example.com")
    account_id = _create_account(client, headers)
    mapping = {
        "date_column": "Data", "date_format": "%d/%m/%Y", "decimal_separator": ",",
        "description_column": "Descrição", "amount_column": "Valor", "invert_sign": True,
    }

    inverted = _preview(client, headers, account_id, mapping=mapping)
    bad_format = _preview(client, headers, account_id, mapping={**mapping, "date_format": "%Y%m%d%H"})

    assert [r["type"] for r in inverted.json()["rows"]] == ["income", "expense", "income"]
    assert bad_format.status_code == 422


def test_confirm_validates_payload(client):
    headers = _register_and_login(client, "imp13@example.com")
    account_id = _create_account(client, headers)
    category_id = _create_category(client, headers)
    body = _preview(client, headers, account_id).json()
    confirm = _confirm_body(account_id, category_id, body)

    negative = {**confirm, "rows": [{**confirm["rows"][0], "amount": "-1.00"}]}
    bad_total = {**confirm, "rows_total": 1}
    empty = {**confirm, "rows": []}

    for payload in (negative, bad_total, empty):
        assert client.post("/statement-imports", headers=headers, json=payload).status_code == 422
