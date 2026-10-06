"""Parser genérico de extrato CSV (RF-011).

Cada banco exporta de um jeito, então nada aqui é específico de banco: o parser
detecta encoding, separador, linha de cabeçalho, colunas, formato de data e
separador decimal, e o usuário pode corrigir qualquer um deles pela tela de
pré-visualização (o `ColumnMapping` volta no preview e pode ser reenviado).

Função pura: sem banco, sem I/O, para ser testável isoladamente (SEC-004: erro
de parsing vira mensagem, nunca exceção não tratada).
"""

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

MAX_ROWS = 5000
DATE_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%Y"]
DELIMITERS = [";", ",", "\t", "|"]
MAX_ABS_AMOUNT = Decimal("9999999999.99")  # Numeric(12, 2) de transactions.amount
MAX_DESCRIPTION = 255

_DATE_KEYWORDS = ("data", "date")
_DESCRIPTION_KEYWORDS = ("descri", "historico", "lancamento", "estabelecimento", "memo", "detalhe", "title")
_AMOUNT_KEYWORDS = ("valor", "amount", "montante")
_DEBIT_KEYWORDS = ("debito", "saida")
_CREDIT_KEYWORDS = ("credito", "entrada")


class CsvParseError(Exception):
    pass


class TooManyRowsError(CsvParseError):
    pass


@dataclass(frozen=True)
class ColumnMapping:
    date_column: str
    date_format: str
    decimal_separator: str
    description_column: str | None = None
    amount_column: str | None = None
    debit_column: str | None = None
    credit_column: str | None = None
    # Alguns bancos exportam despesa como valor positivo; inverte receita/despesa.
    invert_sign: bool = False


@dataclass
class ParsedRow:
    row_number: int
    occurred_at: date | None = None
    type: str | None = None  # "income" | "expense"
    amount: Decimal | None = None
    description: str | None = None
    error: str | None = None


@dataclass
class ParseResult:
    encoding: str
    delimiter: str
    headers: list[str]
    # None quando não deu para adivinhar as colunas: o usuário escolhe na tela.
    mapping: ColumnMapping | None
    rows: list[ParsedRow] = field(default_factory=list)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).strip().lower()


def decode(raw: bytes) -> tuple[str, str]:
    if b"\x00" in raw:
        raise CsvParseError("o arquivo nao parece ser um CSV de texto")
    try:
        return raw.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        # Extrato de banco brasileiro costuma vir em Windows-1252/Latin-1.
        return raw.decode("latin-1"), "latin-1"


def detect_delimiter(text: str) -> str:
    sample_lines = [line for line in text.splitlines() if line.strip()][:30]
    best_delimiter, best_score = ";", 0
    for delimiter in DELIMITERS:
        lengths = [len(row) for row in csv.reader(sample_lines, delimiter=delimiter)]
        if not lengths:
            continue
        modal = max(set(lengths), key=lengths.count)
        score = lengths.count(modal) if modal > 1 else 0
        if score > best_score:
            best_delimiter, best_score = delimiter, score
    return best_delimiter


def _find_header_index(rows: list[list[str]]) -> int:
    keyword_groups = (
        _DATE_KEYWORDS, _DESCRIPTION_KEYWORDS, _AMOUNT_KEYWORDS, _DEBIT_KEYWORDS, _CREDIT_KEYWORDS
    )
    for index, row in enumerate(rows):
        cells = [_normalize(cell) for cell in row]
        hits = sum(1 for group in keyword_groups if any(k in cell for cell in cells for k in group))
        if hits >= 2:
            return index
    # Sem palavras-chave reconhecíveis: primeira linha com pelo menos 2 células preenchidas.
    for index, row in enumerate(rows):
        if sum(1 for cell in row if cell.strip()) >= 2:
            return index
    raise CsvParseError("nao foi possivel encontrar o cabecalho do arquivo")


def _first_header(headers: list[str], keywords: tuple[str, ...], exclude: set[str]) -> str | None:
    for header in headers:
        if header in exclude or not header.strip():
            continue
        if any(keyword in _normalize(header) for keyword in keywords):
            return header
    return None


def _guess_date_format(values: list[str]) -> str:
    samples = [v.strip() for v in values if v.strip()][:50]

    def hits(fmt: str) -> int:
        count = 0
        for value in samples:
            try:
                datetime.strptime(value, fmt)
                count += 1
            except ValueError:
                pass
        return count

    return max(DATE_FORMATS, key=lambda fmt: (hits(fmt), -DATE_FORMATS.index(fmt)))


def _guess_decimal_separator(values: list[str]) -> str:
    cleaned = [v.strip() for v in values if v.strip()]
    if any(re.search(r",\d{1,2}\s*[-)dDcC]?$", v) for v in cleaned):
        return ","
    if any(re.search(r"\.\d{1,2}\s*[-)dDcC]?$", v) for v in cleaned):
        return "."
    return ","


def guess_mapping(headers: list[str], data_rows: list[list[str]]) -> ColumnMapping | None:
    column = {name: [row[i] if i < len(row) else "" for row in data_rows] for i, name in enumerate(headers)}

    date_column = _first_header(headers, _DATE_KEYWORDS, exclude=set())
    amount_column = _first_header(headers, _AMOUNT_KEYWORDS, exclude={date_column or ""})
    debit_column = _first_header(headers, _DEBIT_KEYWORDS, exclude={date_column or ""})
    credit_column = _first_header(headers, _CREDIT_KEYWORDS, exclude={date_column or ""})
    if date_column is None or not (amount_column or (debit_column and credit_column)):
        return None

    used = {date_column, amount_column or "", debit_column or "", credit_column or ""}
    description_column = _first_header(headers, _DESCRIPTION_KEYWORDS, exclude=used)

    amount_headers = [h for h in (amount_column, debit_column, credit_column) if h]
    amount_values = [v for h in amount_headers for v in column[h]]
    return ColumnMapping(
        date_column=date_column,
        date_format=_guess_date_format(column[date_column]),
        decimal_separator=_guess_decimal_separator(amount_values),
        description_column=description_column,
        # Uma coluna de valor com sinal tem prioridade sobre débito/crédito separados.
        amount_column=amount_column,
        debit_column=None if amount_column else debit_column,
        credit_column=None if amount_column else credit_column,
    )


def parse_amount(text: str, decimal_separator: str) -> Decimal:
    """Devolve o valor COM sinal. Aceita 'R$ 1.234,56', '-10,00', '(10,00)', '10,00-', '10,00D'."""
    value = text.strip().replace("R$", "").replace(" ", "").replace(" ", "")
    if not value:
        raise ValueError("valor vazio")

    negative = False
    if value.startswith("(") and value.endswith(")"):
        negative, value = True, value[1:-1]
    if value and value.endswith("-"):
        negative, value = True, value[:-1]
    elif value and value[-1] in "dD":
        negative, value = True, value[:-1]
    elif value and value[-1] in "cC":
        value = value[:-1]
    if value.startswith("-"):
        negative, value = True, value[1:]
    elif value.startswith("+"):
        value = value[1:]

    thousands = "." if decimal_separator == "," else ","
    value = value.replace(thousands, "")
    if decimal_separator == ",":
        value = value.replace(",", ".")

    if not re.fullmatch(r"\d+(\.\d+)?", value):
        raise ValueError(f"valor invalido: {text.strip()!r}")
    if "." in value and len(value.split(".")[1].rstrip("0")) > 2:
        raise ValueError(f"valor com mais de 2 casas decimais: {text.strip()!r}")

    try:
        amount = Decimal(value).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValueError(f"valor invalido: {text.strip()!r}")
    if amount > MAX_ABS_AMOUNT:
        raise ValueError("valor alto demais")
    return -amount if negative else amount


def _cell(row: list[str], index: dict[str, int], column: str | None) -> str:
    if column is None:
        return ""
    position = index[column]
    return row[position].strip() if position < len(row) else ""


def _parse_row(row_number: int, row: list[str], index: dict[str, int], mapping: ColumnMapping) -> ParsedRow | None:
    date_text = _cell(row, index, mapping.date_column)
    amount_text = _cell(row, index, mapping.amount_column)
    debit_text = _cell(row, index, mapping.debit_column)
    credit_text = _cell(row, index, mapping.credit_column)
    if not date_text and not (amount_text or debit_text or credit_text):
        return None  # linha em branco ou rodapé sem dados

    parsed = ParsedRow(row_number=row_number)
    try:
        try:
            parsed.occurred_at = datetime.strptime(date_text, mapping.date_format).date()
        except ValueError:
            raise ValueError(f"data invalida: {date_text!r}" if date_text else "data ausente")

        if mapping.amount_column:
            signed = parse_amount(amount_text, mapping.decimal_separator)
        else:
            debit = parse_amount(debit_text, mapping.decimal_separator) if debit_text else Decimal(0)
            credit = parse_amount(credit_text, mapping.decimal_separator) if credit_text else Decimal(0)
            if debit and credit:
                raise ValueError("debito e credito preenchidos na mesma linha")
            signed = -abs(debit) if debit else abs(credit)

        if signed == 0:
            raise ValueError("valor zero")
        if mapping.invert_sign:
            signed = -signed

        parsed.type = "expense" if signed < 0 else "income"
        parsed.amount = abs(signed)
        description = " ".join(_cell(row, index, mapping.description_column).split())
        parsed.description = description[:MAX_DESCRIPTION] or None
    except ValueError as exc:
        parsed.error = str(exc)
    return parsed


def parse_csv(raw: bytes, mapping: ColumnMapping | None = None) -> ParseResult:
    text, encoding = decode(raw)
    delimiter = detect_delimiter(text)
    all_rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if not any(any(cell.strip() for cell in row) for row in all_rows):
        raise CsvParseError("o arquivo esta vazio")

    header_index = _find_header_index(all_rows)
    headers = [cell.strip() for cell in all_rows[header_index]]
    data = [(i + 1, row) for i, row in enumerate(all_rows) if i > header_index]
    data = [(number, row) for number, row in data if any(cell.strip() for cell in row)]
    if len(data) > MAX_ROWS:
        raise TooManyRowsError(f"o arquivo tem mais de {MAX_ROWS} linhas")

    result = ParseResult(encoding=encoding, delimiter=delimiter, headers=headers, mapping=None)
    chosen = mapping or guess_mapping(headers, [row for _, row in data])
    if chosen is None:
        return result

    index = {}
    for position, name in enumerate(headers):
        index.setdefault(name, position)
    for column in (
        chosen.date_column, chosen.description_column, chosen.amount_column,
        chosen.debit_column, chosen.credit_column,
    ):
        if column is not None and column not in index:
            raise CsvParseError(f"a coluna {column!r} nao existe no arquivo")
    if not chosen.amount_column and not (chosen.debit_column or chosen.credit_column):
        raise CsvParseError("informe a coluna de valor (ou de debito/credito)")

    result.mapping = chosen
    for number, row in data:
        parsed = _parse_row(number, row, index, chosen)
        if parsed is not None:
            result.rows.append(parsed)
    return result
