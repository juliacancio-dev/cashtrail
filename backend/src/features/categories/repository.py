import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.categories.models import Category


def list_by_user(db: Session, user_id: uuid.UUID) -> list[Category]:
    return list(db.scalars(select(Category).where(Category.user_id == user_id).order_by(Category.created_at)))


def get_by_id_and_user(db: Session, category_id: uuid.UUID, user_id: uuid.UUID) -> Category | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )


def create(db: Session, user_id: uuid.UUID, name: str) -> Category:
    category = Category(user_id=user_id, name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def rename(db: Session, category: Category, name: str) -> Category:
    category.name = name
    db.commit()
    db.refresh(category)
    return category


def archive(db: Session, category: Category) -> Category:
    category.is_archived = True
    db.commit()
    db.refresh(category)
    return category
