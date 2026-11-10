import csv
import io
import uuid
from datetime import UTC, datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import Item, ItemCreate, User, UserCreate
from tests.utils.item import create_random_item
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

CSV_HEADER = ["id", "title", "description", "created_at"]


def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_read_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_update_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Item deleted successfully"


def test_delete_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_items_count(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Create some items
    create_random_item(db)
    create_random_item(db)
    create_random_item(db)

    # Test the count endpoint
    response = client.get(
        f"{settings.API_V1_STR}/items/count",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    count = response.json()
    assert isinstance(count, int)
    assert count >= 3


def test_read_items_count_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # Create an item owned by the logged-in normal user
    user = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert user
    item_in = ItemCreate(title=random_lower_string(), description="Mine")
    crud.create_item(session=db, item_in=item_in, owner_id=user.id)
    create_random_item(db)

    # Test the count endpoint for normal user (should only count their own items)
    response = client.get(
        f"{settings.API_V1_STR}/items/count",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    count = response.json()
    assert isinstance(count, int)
    assert count >= 1


def test_export_items_csv(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    user = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert user
    own_item = crud.create_item(
        session=db,
        item_in=ItemCreate(title='Export, "me"', description="Mine"),
        owner_id=user.id,
    )
    other_item = create_random_item(db)

    response = client.get(
        f"{settings.API_V1_STR}/items/export",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "items.csv" in response.headers["content-disposition"]

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == CSV_HEADER
    ids = {row[0] for row in rows[1:]}
    assert str(own_item.id) in ids
    assert str(other_item.id) not in ids
    own_row = next(row for row in rows[1:] if row[0] == str(own_item.id))
    assert own_row[:3] == [str(own_item.id), own_item.title, "Mine"]


def test_export_items_csv_superuser_only_own_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    other_item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/export",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert str(other_item.id) not in response.text


def test_export_items_csv_unauthenticated(client: TestClient, db: Session) -> None:
    item = create_random_item(db)
    response = client.get(f"{settings.API_V1_STR}/items/export")
    assert response.status_code == 401
    assert not response.headers["content-type"].startswith("text/csv")
    assert "content-disposition" not in response.headers
    assert item.title not in response.text
    assert str(item.id) not in response.text


def _create_user_with_headers(
    client: TestClient, db: Session
) -> tuple[User, dict[str, str]]:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    headers = user_authentication_headers(client=client, email=email, password=password)
    return user, headers


def _export_rows(client: TestClient, headers: dict[str, str]) -> list[list[str]]:
    response = client.get(f"{settings.API_V1_STR}/items/export", headers=headers)
    assert response.status_code == 200
    return list(csv.reader(io.StringIO(response.text, newline="")))


def _create_item_at(
    db: Session, owner: User, created_at: datetime | None, title: str = "Timed"
) -> Item:
    item = crud.create_item(
        session=db, item_in=ItemCreate(title=title), owner_id=owner.id
    )
    item.created_at = created_at
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_export_items_csv_has_a_row_for_every_item_beyond_one_page(
    client: TestClient, db: Session
) -> None:
    user, headers = _create_user_with_headers(client, db)
    # More than the largest table page (50) and the Items page's read limit (100)
    items = [
        crud.create_item(
            session=db,
            item_in=ItemCreate(title=f"Item {index}"),
            owner_id=user.id,
        )
        for index in range(105)
    ]

    rows = _export_rows(client, headers)

    assert rows[0] == CSV_HEADER
    assert len(rows) == len(items) + 1
    assert {row[0] for row in rows[1:]} == {str(item.id) for item in items}


def test_export_items_csv_created_at_is_the_creation_time_in_utc(
    client: TestClient, db: Session
) -> None:
    user, headers = _create_user_with_headers(client, db)
    known_time = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)
    item = _create_item_at(db, user, known_time)

    rows = _export_rows(client, headers)

    assert rows[0] == CSV_HEADER
    row = next(row for row in rows[1:] if row[0] == str(item.id))
    exported = datetime.fromisoformat(row[3])
    assert exported == known_time
    assert exported.utcoffset() == timedelta(0)


def test_export_items_csv_created_at_converts_other_offsets_to_utc(
    client: TestClient, db: Session
) -> None:
    user, headers = _create_user_with_headers(client, db)
    ist = timezone(timedelta(hours=5, minutes=30))
    item = _create_item_at(db, user, datetime(2026, 3, 4, 5, 6, 7, tzinfo=ist))

    rows = _export_rows(client, headers)

    row = next(row for row in rows[1:] if row[0] == str(item.id))
    exported = datetime.fromisoformat(row[3])
    assert exported.utcoffset() == timedelta(0)
    assert exported == datetime(2026, 3, 3, 23, 36, 7, tzinfo=UTC)


def test_export_items_csv_empty_cells_for_missing_created_at_and_description(
    client: TestClient, db: Session
) -> None:
    user, headers = _create_user_with_headers(client, db)
    item = _create_item_at(db, user, None, title="No date")

    rows = _export_rows(client, headers)

    assert rows == [CSV_HEADER, [str(item.id), "No date", "", ""]]


def test_export_items_csv_each_user_only_gets_their_own_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    normal_user, normal_headers = _create_user_with_headers(client, db)
    normal_item = crud.create_item(
        session=db, item_in=ItemCreate(title="Normal's"), owner_id=normal_user.id
    )
    superuser = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert superuser
    crud.create_item(
        session=db, item_in=ItemCreate(title="Super's"), owner_id=superuser.id
    )
    superuser_item_ids = {
        str(item_id)
        for item_id in db.exec(select(Item.id).where(Item.owner_id == superuser.id))
    }

    normal_rows = _export_rows(client, normal_headers)
    superuser_rows = _export_rows(client, superuser_token_headers)

    assert normal_rows[0] == CSV_HEADER
    assert [row[0] for row in normal_rows[1:]] == [str(normal_item.id)]
    assert superuser_rows[0] == CSV_HEADER
    assert {row[0] for row in superuser_rows[1:]} == superuser_item_ids


def test_export_items_csv_no_items_returns_only_the_header(
    client: TestClient, db: Session
) -> None:
    _, headers = _create_user_with_headers(client, db)

    response = client.get(f"{settings.API_V1_STR}/items/export", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "items.csv" in response.headers["content-disposition"]
    assert list(csv.reader(io.StringIO(response.text, newline=""))) == [CSV_HEADER]


def test_export_items_csv_keeps_special_characters_in_one_cell(
    client: TestClient, db: Session
) -> None:
    user, headers = _create_user_with_headers(client, db)
    title = 'Comma, "quote"\nand line break'
    description = 'first, "line"\r\nsecond line'
    item = crud.create_item(
        session=db,
        item_in=ItemCreate(title=title, description=description),
        owner_id=user.id,
    )

    rows = _export_rows(client, headers)

    assert rows[0] == CSV_HEADER
    assert len(rows) == 2
    assert len(rows[1]) == len(CSV_HEADER)
    assert rows[1][:3] == [str(item.id), title, description]
