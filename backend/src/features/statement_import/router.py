import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.core.rate_limit import limiter
from src.features.statement_import import parser, service
from src.features.statement_import.parser import ColumnMapping
from src.features.statement_import.schemas import (
    ColumnMappingSchema,
    ConfirmRequest,
    ConfirmResponse,
    DuplicateOf,
    PreviewResponse,
    PreviewRow,
)
from src.features.transactions import service as transactions_service

router = APIRouter(prefix="/statement-imports", tags=["statement-imports"])

# SEC-004: limite de tamanho e de tipo. Extrato mensal em CSV tem poucas centenas de KB.
MAX_FILE_BYTES = 2 * 1024 * 1024


@router.post("/preview", response_model=PreviewResponse)
@limiter.limit("10/minute")
def preview_import(
    request: Request,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    account_id: Annotated[uuid.UUID, Form()],
    mapping: Annotated[str | None, Form()] = None,
) -> PreviewResponse:
    file_name = file.filename or "extrato.csv"
    if not file_name.lower().endswith(".csv"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="envie um arquivo .csv")

    raw = file.file.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"arquivo maior que o limite de {MAX_FILE_BYTES // (1024 * 1024)} MB",
        )

    parsed_mapping: ColumnMapping | None = None
    if mapping:
        try:
            parsed_mapping = ColumnMapping(**ColumnMappingSchema.model_validate_json(mapping).model_dump())
        except ValidationError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="mapeamento de colunas invalido")

    try:
        result = service.preview(db, current_user.id, account_id, raw, parsed_mapping)
    except service.AccountNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")
    except service.ArchivedAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos")
    except parser.CsvParseError as exc:  # inclui TooManyRowsError
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))

    return PreviewResponse(
        file_name=file_name[:255],
        file_sha256=result.file_sha256,
        encoding=result.parsed.encoding,
        delimiter=result.parsed.delimiter,
        headers=result.parsed.headers,
        mapping=ColumnMappingSchema(**vars(result.parsed.mapping)) if result.parsed.mapping else None,
        rows=[
            PreviewRow(
                row_number=row.row_number,
                occurred_at=row.occurred_at,
                type=row.type,
                amount=row.amount,
                description=row.description,
                error=row.error,
                duplicate_of=(
                    DuplicateOf.model_validate(result.duplicates[row.row_number])
                    if row.row_number in result.duplicates
                    else None
                ),
            )
            for row in result.parsed.rows
        ],
        previously_imported_at=result.previously_imported_at,
    )


@router.post("", response_model=ConfirmResponse, status_code=status.HTTP_201_CREATED)
def confirm_import(
    payload: ConfirmRequest, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> ConfirmResponse:
    try:
        statement_import = service.confirm_import(
            db,
            current_user.id,
            account_id=payload.account_id,
            file_name=payload.file_name,
            file_sha256=payload.file_sha256,
            rows_total=payload.rows_total,
            rows=[
                service.ConfirmedRow(
                    occurred_at=row.occurred_at,
                    type=row.type,
                    amount=row.amount,
                    description=row.description,
                    category_id=row.category_id,
                )
                for row in payload.rows
            ],
        )
    except service.AccountNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")
    except transactions_service.ArchivedAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos")
    except transactions_service.InvalidCategoryError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")

    return ConfirmResponse.model_validate(statement_import)
