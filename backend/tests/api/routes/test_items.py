import csv
import io
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import ItemCreate
from tests.utils.item import create_random_item
from tests.utils.user import authentication_token_from_email, create_random_user
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


def _search_user_headers(
    client: TestClient, db: Session
) -> tuple[uuid.UUID, dict[str, str]]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = crud.get_user_by_email(session=db, email=email)
    assert user
    return user.id, headers


def test_search_items_own_items_case_insensitive(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _search_user_headers(client, db)
    widget = crud.create_item(
        session=db, item_in=ItemCreate(title="Blue Widget"), owner_id=user_id
    )
    gadget = crud.create_item(
        session=db, item_in=ItemCreate(title="blue gadget"), owner_id=user_id
    )
    crud.create_item(session=db, item_in=ItemCreate(title="Red Box"), owner_id=user_id)
    other_user = create_random_user(db)
    other_item = crud.create_item(
        session=db, item_in=ItemCreate(title="other blue"), owner_id=other_user.id
    )

    response = client.get(
        f"{settings.API_V1_STR}/items/search", headers=headers, params={"q": " blue "}
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2
    ids = [item["id"] for item in content["data"]]
    assert ids == [str(gadget.id), str(widget.id)]
    assert str(other_item.id) not in ids


def test_search_items_superuser_sees_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    token = random_lower_string()
    items = [
        crud.create_item(
            session=db,
            item_in=ItemCreate(title=f"Blue {token}"),
            owner_id=create_random_user(db).id,
        )
        for _ in range(2)
    ]
    response = client.get(
        f"{settings.API_V1_STR}/items/search",
        headers=superuser_token_headers,
        params={"q": f"BLUE {token}"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2
    assert {item["id"] for item in content["data"]} == {str(i.id) for i in items}


def test_search_items_no_match(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/search",
        headers=normal_user_token_headers,
        params={"q": random_lower_string()},
    )
    assert response.status_code == 200
    assert response.json() == {"data": [], "count": 0}


def test_search_items_wildcards_are_literal(client: TestClient, db: Session) -> None:
    user_id, headers = _search_user_headers(client, db)
    literal = crud.create_item(
        session=db, item_in=ItemCreate(title="100% off_sale"), owner_id=user_id
    )
    crud.create_item(
        session=db, item_in=ItemCreate(title="100 offXsale"), owner_id=user_id
    )
    for q in ["%", "_", "% off_"]:
        response = client.get(
            f"{settings.API_V1_STR}/items/search", headers=headers, params={"q": q}
        )
        assert response.status_code == 200
        content = response.json()
        assert content["count"] == 1
        assert content["data"][0]["id"] == str(literal.id)


def test_search_items_invalid_query(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    url = f"{settings.API_V1_STR}/items/search"
    for params in [{}, {"q": ""}, {"q": "   "}, {"q": "a" * 256}]:
        response = client.get(url, headers=normal_user_token_headers, params=params)
        assert response.status_code == 422, params


def test_search_items_unauthenticated(client: TestClient) -> None:
    url = f"{settings.API_V1_STR}/items/search"
    response = client.get(url, params={"q": "blue"})
    assert response.status_code == 401
    assert (
        response.status_code == client.get(f"{settings.API_V1_STR}/items/").status_code
    )
    response = client.get(
        url, params={"q": "blue"}, headers={"Authorization": "Bearer invalid"}
    )
    invalid_list = client.get(
        f"{settings.API_V1_STR}/items/", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == invalid_list.status_code
    assert response.json() == invalid_list.json()


def test_search_items_pagination(client: TestClient, db: Session) -> None:
    user_id, headers = _search_user_headers(client, db)
    created = [
        crud.create_item(
            session=db, item_in=ItemCreate(title=f"blue {i}"), owner_id=user_id
        )
        for i in range(3)
    ]
    response = client.get(
        f"{settings.API_V1_STR}/items/search",
        headers=headers,
        params={"q": "blue", "skip": 0, "limit": 2},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 3
    assert [item["id"] for item in content["data"]] == [
        str(created[2].id),
        str(created[1].id),
    ]


def test_search_route_not_shadowed_by_read_item(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/search",
        headers=normal_user_token_headers,
        params={"q": "x"},
    )
    assert response.status_code == 200
    assert set(response.json()) == {"data", "count"}
