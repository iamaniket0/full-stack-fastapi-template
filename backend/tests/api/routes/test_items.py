import csv
import io
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app import crud
from app.core.config import settings
from app.models import Item, ItemCreate, User, UserCreate
from tests.utils.item import create_random_item
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


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


def _user_headers(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    headers = user_authentication_headers(client=client, email=email, password=password)
    return user, headers


def _create_item_for(db: Session, user: User) -> Item:
    item_in = ItemCreate(title=random_lower_string(), description="Mine")
    return crud.create_item(session=db, item_in=item_in, owner_id=user.id)


def test_read_items_count_normal_user_owns_three(
    client: TestClient, db: Session
) -> None:
    user, headers = _user_headers(client, db)
    for _ in range(3):
        _create_item_for(db, user)
    response = client.get(f"{settings.API_V1_STR}/items/count", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"count": 3}


def test_read_items_count_normal_user_owns_none(
    client: TestClient, db: Session
) -> None:
    create_random_item(db)
    _, headers = _user_headers(client, db)
    response = client.get(f"{settings.API_V1_STR}/items/count", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"count": 0}


def test_read_items_count_only_own_items(client: TestClient, db: Session) -> None:
    user_a, headers_a = _user_headers(client, db)
    user_b, headers_b = _user_headers(client, db)
    for _ in range(2):
        _create_item_for(db, user_a)
    for _ in range(4):
        _create_item_for(db, user_b)
    response = client.get(f"{settings.API_V1_STR}/items/count", headers=headers_a)
    assert response.status_code == 200
    assert response.json() == {"count": 2}
    response = client.get(f"{settings.API_V1_STR}/items/count", headers=headers_b)
    assert response.status_code == 200
    assert response.json() == {"count": 4}


def test_read_items_count_superuser_counts_all_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    create_random_item(db)
    total = db.exec(select(func.count()).select_from(Item)).one()
    response = client.get(
        f"{settings.API_V1_STR}/items/count",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"count": total}


def test_read_items_count_changes_on_create_and_delete(
    client: TestClient, db: Session
) -> None:
    _, headers = _user_headers(client, db)
    url = f"{settings.API_V1_STR}/items/count"

    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"count": 0}

    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": "Foo", "description": "Bar"},
    )
    assert response.status_code == 200
    item_id = response.json()["id"]

    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"count": 1}

    response = client.delete(f"{settings.API_V1_STR}/items/{item_id}", headers=headers)
    assert response.status_code == 200

    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"count": 0}


def test_read_items_count_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/items/count")
    assert response.status_code == 401
    assert "count" not in response.json()


def test_read_items_count_invalid_token(client: TestClient) -> None:
    headers = {"Authorization": "Bearer invalid-token"}
    count_response = client.get(f"{settings.API_V1_STR}/items/count", headers=headers)
    list_response = client.get(f"{settings.API_V1_STR}/items/", headers=headers)
    assert count_response.status_code in (401, 403)
    assert count_response.status_code == list_response.status_code
    assert "count" not in count_response.json()


def test_read_items_count_openapi_schema(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    operation = openapi["paths"][f"{settings.API_V1_STR}/items/count"]["get"]
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        schema = openapi["components"]["schemas"][name]
    assert schema.get("type") == "object"
    assert list(schema["properties"].keys()) == ["count"]
    assert schema["properties"]["count"]["type"] == "integer"


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
    assert rows[0] == ["id", "title", "description"]
    ids = {row[0] for row in rows[1:]}
    assert str(own_item.id) in ids
    assert str(other_item.id) not in ids
    assert [str(own_item.id), own_item.title, "Mine"] in rows[1:]


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


def test_export_items_csv_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/items/export")
    assert response.status_code == 401
