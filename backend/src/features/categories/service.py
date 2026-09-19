import uuid

from sqlalchemy.orm import Session

from src.features.categories import repository
from src.features.categories.models import Category


class CategoryNotFoundError(Exception):
    pass


def list_categories(db: Session, user_id: uuid.UUID) -> list[Category]:
    return repository.list_by_user(db, user_id)


def create_category(db: Session, user_id: uuid.UUID, name: str) -> Category:
    return repository.create(db, user_id=user_id, name=name)


def get_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    category = repository.get_by_id_and_user(db, category_id, user_id)
    if category is None:
        raise CategoryNotFoundError(category_id)

    return category


def rename_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, name: str) -> Category:
    category = get_category(db, user_id, category_id)
    return repository.rename(db, category, name)


def archive_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    category = get_category(db, user_id, category_id)
    return repository.archive(db, category)
