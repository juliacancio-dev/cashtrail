import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.features.statement_import.parser import DATE_FORMATS, MAX_ROWS

# Mesma lista do parser, como Literal: o formato de data nunca vem livre do cliente.
DateFormat = Literal["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%Y"]
assert set(DateFormat.__args__) == set(DATE_FORMATS)


class ColumnMappingSchema(BaseModel):
    date_column: str = Field(min_length=1, max_length=255)
    date_format: DateFormat
    decimal_separator: Literal[",", "."]
    description_column: str | None = Field(default=None, max_length=255)
    amount_column: str | None = Field(default=None, max_length=255)
    debit_column: str | None = Field(default=None, max_length=255)
    credit_column: str | None = Field(default=None, max_length=255)
    invert_sign: bool = False


class DuplicateOf(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    occurred_at: date
    amount: Decimal
    description: str | None


class PreviewRow(BaseModel):
    row_number: int
    occurred_at: date | None
    type: Literal["income", "expense"] | None
    amount: Decimal | None
    description: str | None
    error: str | None
    duplicate_of: DuplicateOf | None


class PreviewResponse(BaseModel):
    file_name: str
    file_sha256: str
    encoding: str
    delimiter: str
    headers: list[str]
    mapping: ColumnMappingSchema | None
    rows: list[PreviewRow]
    previously_imported_at: datetime | None


class ConfirmRow(BaseModel):
    occurred_at: date
    type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)
    category_id: uuid.UUID


class ConfirmRequest(BaseModel):
    account_id: uuid.UUID
    file_name: str = Field(min_length=1, max_length=255)
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rows_total: int = Field(ge=1, le=MAX_ROWS)
    rows: list[ConfirmRow] = Field(min_length=1, max_length=MAX_ROWS)

    @model_validator(mode="after")
    def rows_total_covers_rows(self) -> "ConfirmRequest":
        if self.rows_total < len(self.rows):
            raise ValueError("rows_total nao pode ser menor que o numero de linhas confirmadas")
        return self


class ConfirmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rows_total: int
    transactions_created: int
    rows_skipped: int
