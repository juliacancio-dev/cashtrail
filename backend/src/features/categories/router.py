import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.categories import service
from src.features.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[CategoryRead]:
    categories = service.list_categories(db, current_user.id)
    return [CategoryRead.model_validate(c) for c in categories]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> CategoryRead:
    category = service.create_category(db, current_user.id, payload.name, payload.dre_group)
    return CategoryRead.model_validate(category)


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> CategoryRead:
    try:
        category = service.get_category(db, current_user.id, category_id)
    except service.CategoryNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")

    return CategoryRead.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CategoryRead:
    try:
        changes = payload.model_dump(exclude_unset=True)
        if changes.get("name") is None:
            changes.pop("name", None)  # `name: null` não renomeia; `dre_group: null` remove o grupo
        category = service.update_category(db, current_user.id, category_id, changes)
    except service.CategoryNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")

    return CategoryRead.model_validate(category)


@router.post("/{category_id}/archive", response_model=CategoryRead)
def archive_category(
    category_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> CategoryRead:
    try:
        category = service.archive_category(db, current_user.id, category_id)
    except service.CategoryNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")

    return CategoryRead.model_validate(category)
