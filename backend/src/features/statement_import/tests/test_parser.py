"""RF-011: parser genérico de CSV. Amostras sintéticas de formatos comuns de banco."""

from datetime import date
from decimal import Decimal

import pytest

from src.features.statement_import import parser
from src.features.statement_import.parser import ColumnMapping, CsvParseError, parse_amount, parse_csv

# Valor com sinal numa coluna só, ';' como separador, vírgula decimal, UTF-8.
SIGNED_COLUMN_CSV = (
    "Data;Descrição;Valor\n"
    "10/09/2026;PADARIA CENTRAL;-12,50\n"
    "11/09/2026;SALARIO EMPRESA;5.000,00\n"
    "12/09/2026;MERCADO BAIRRO;-1.234,56\n"
).encode("utf-8")

# Débito e crédito em colunas separadas, Latin-1, linhas de cabeçalho do banco antes da tabela.
DEBIT_CREDIT_CSV = (
    "Extrato conta corrente\n"
    "Agência: 0001;Conta: 12345-6\n"
    "\n"
    "Data Lançamento;Histórico;Débito;Crédito;Saldo\n"
    "10/09/2026;Pagamento boleto;150,00;;1.000,00\n"
    "11/09/2026;Pix recebido;;300,00;1.300,00\n"
).encode("latin-1")

# Estilo "internacional": vírgula como separador, ponto decimal, data ISO.
ISO_CSV = "date,description,amount\n2026-09-10,Coffee,-4.50\n2026-09-11,Refund,20.00\n".encode("utf-8")


def test_parses_signed_amount_column_and_guesses_mapping():
    result = parse_csv(SIGNED_COLUMN_CSV)

    assert result.delimiter == ";"
    assert result.mapping.date_column == "Data"
    assert result.mapping.date_format == "%d/%m/%Y"
    assert result.mapping.decimal_separator == ","
    assert [(r.type, r.amount, r.description) for r in result.rows] == [
        ("expense", Decimal("12.50"), "PADARIA CENTRAL"),
        ("income", Decimal("5000.00"), "SALARIO EMPRESA"),
        ("expense", Decimal("1234.56"), "MERCADO BAIRRO"),
    ]
    assert result.rows[0].occurred_at == date(2026, 9, 10)


def test_parses_debit_credit_columns_latin1_and_skips_preamble():
    result = parse_csv(DEBIT_CREDIT_CSV)

    assert result.encoding == "latin-1"
    assert result.headers[:4] == ["Data Lançamento", "Histórico", "Débito", "Crédito"]
    assert result.mapping.date_column == "Data Lançamento"
    assert result.mapping.description_column == "Histórico"
    assert [(r.type, r.amount) for r in result.rows] == [
        ("expense", Decimal("150.00")),
        ("income", Decimal("300.00")),
    ]


def test_parses_iso_dates_and_dot_decimal():
    result = parse_csv(ISO_CSV)

    assert result.delimiter == ","
    assert result.mapping.date_format == "%Y-%m-%d"
    assert result.mapping.decimal_separator == "."
    assert [(r.type, r.amount) for r in result.rows] == [("expense", Decimal("4.50")), ("income", Decimal("20.00"))]


def test_explicit_mapping_overrides_guess_and_invert_sign():
    mapping = ColumnMapping(
        date_column="Data", date_format="%d/%m/%Y", decimal_separator=",",
        description_column="Descrição", amount_column="Valor", invert_sign=True,
    )

    result = parse_csv(SIGNED_COLUMN_CSV, mapping)

    assert [r.type for r in result.rows] == ["income", "expense", "income"]


def test_unknown_columns_return_no_mapping_so_user_can_choose():
    result = parse_csv(b"col_a;col_b;col_c\n1;2;3\n4;5;6\n")

    assert result.mapping is None
    assert result.headers == ["col_a", "col_b", "col_c"]
    assert result.rows == []


def test_bad_rows_report_error_without_aborting_the_file():
    csv_bytes = b"Data;Descricao;Valor\n10/09/2026;ok;-10,00\n31/31/2026;data ruim;-5,00\n11/09/2026;valor ruim;abc\n12/09/2026;zero;0,00\n"

    result = parse_csv(csv_bytes)

    assert [r.error is None for r in result.rows] == [True, False, False, False]
    assert "data invalida" in result.rows[1].error
    assert "valor invalido" in result.rows[2].error
    assert result.rows[3].error == "valor zero"
    assert [r.row_number for r in result.rows] == [2, 3, 4, 5]


def test_blank_and_footer_rows_are_ignored():
    result = parse_csv(b"Data;Descricao;Valor\n10/09/2026;a;-1,00\n\n;;\n")

    assert len(result.rows) == 1


def test_mapping_with_missing_column_is_rejected():
    mapping = ColumnMapping(date_column="Inexistente", date_format="%d/%m/%Y", decimal_separator=",", amount_column="Valor")

    with pytest.raises(CsvParseError, match="nao existe"):
        parse_csv(SIGNED_COLUMN_CSV, mapping)


@pytest.mark.parametrize("content", [b"", b"\n\n  \n", b"\x00\x01\x02binary"])
def test_empty_or_binary_file_is_rejected(content):
    with pytest.raises(CsvParseError):
        parse_csv(content)


def test_too_many_rows_is_rejected(monkeypatch):
    monkeypatch.setattr(parser, "MAX_ROWS", 3)
    rows = "\n".join(f"10/09/2026;linha {i};-1,00" for i in range(4))

    with pytest.raises(parser.TooManyRowsError):
        parse_csv(f"Data;Descricao;Valor\n{rows}\n".encode())


@pytest.mark.parametrize(
    ("text", "separator", "expected"),
    [
        ("R$ 1.234,56", ",", Decimal("1234.56")),
        ("-10,00", ",", Decimal("-10.00")),
        ("(10,00)", ",", Decimal("-10.00")),
        ("10,00-", ",", Decimal("-10.00")),
        ("10,00D", ",", Decimal("-10.00")),
        ("10,00C", ",", Decimal("10.00")),
        ("+7,5", ",", Decimal("7.50")),
        ("1,234.56", ".", Decimal("1234.56")),
        ("-4.5", ".", Decimal("-4.50")),
        ("1000", ",", Decimal("1000.00")),
    ],
)
def test_parse_amount_formats(text, separator, expected):
    assert parse_amount(text, separator) == expected


@pytest.mark.parametrize("text", ["", "   ", "abc", "()", "-", "1,234,56", "10,005", "99999999999,00"])
def test_parse_amount_rejects_invalid(text):
    with pytest.raises(ValueError):
        parse_amount(text, ",")
