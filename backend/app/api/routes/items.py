import csv
import io
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import ColumnElement
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
) -> Any:
    """
    Retrieve items. Archived items are hidden unless include_archived is true.
    """
    filters: list[ColumnElement[bool]] = []
    if not current_user.is_superuser:
        filters.append(col(Item.owner_id) == current_user.id)
    if not include_archived:
        filters.append(col(Item.archived).is_(False))

    count_statement = select(func.count()).select_from(Item).where(*filters)
    count = session.exec(count_statement).one()
    statement = (
        select(Item)
        .where(*filters)
        .order_by(col(Item.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()

    items_public = [ItemPublic.model_validate(item) for item in items]
    return ItemsPublic(data=items_public, count=count)


@router.get("/count", response_model=int)
def read_items_count(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get total count of items.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Item)
    else:
        count_statement = (
            select(func.count())
            .select_from(Item)
            .where(Item.owner_id == current_user.id)
        )
    count = session.exec(count_statement).one()
    return count


@router.get(
    "/export",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_items(session: SessionDep, current_user: CurrentUser) -> Response:
    """
    Export the current user's own items as CSV (id, title, description).
    """
    statement = (
        select(Item)
        .where(Item.owner_id == current_user.id)
        .order_by(col(Item.created_at).desc())
    )
    items = session.exec(statement).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "title", "description"])
    for item in items:
        writer.writerow([item.id, item.title, item.description or ""])

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="items.csv"'},
    )


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def _set_archived(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID, archived: bool
) -> Item:
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if item.archived != archived:
        item.archived = archived
        session.add(item)
        session.commit()
        session.refresh(item)
    return item


@router.patch("/{id}/archive", response_model=ItemPublic)
def archive_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Archive an item.
    """
    return _set_archived(session, current_user, id, archived=True)


@router.patch("/{id}/unarchive", response_model=ItemPublic)
def unarchive_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Unarchive an item.
    """
    return _set_archived(session, current_user, id, archived=False)


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
