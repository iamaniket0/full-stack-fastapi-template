import uuid

import httpx
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import Item, ItemCreate
from tests.utils.item import create_random_item
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email, random_lower_string


def _create_user_with_headers(
    client: TestClient, db: Session
) -> tuple[uuid.UUID, dict[str, str]]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = crud.get_user_by_email(session=db, email=email)
    assert user is not None
    return user.id, headers


def _create_item(db: Session, owner_id: uuid.UUID) -> Item:
    item_in = ItemCreate(title=random_lower_string(), description=random_lower_string())
    return crud.create_item(session=db, item_in=item_in, owner_id=owner_id)


def _archive(
    client: TestClient, headers: dict[str, str], item_id: uuid.UUID
) -> httpx.Response:
    return client.patch(
        f"{settings.API_V1_STR}/items/{item_id}/archive", headers=headers
    )


def _unarchive(
    client: TestClient, headers: dict[str, str], item_id: uuid.UUID
) -> httpx.Response:
    return client.patch(
        f"{settings.API_V1_STR}/items/{item_id}/unarchive", headers=headers
    )


def _get_archived(
    client: TestClient, superuser_token_headers: dict[str, str], item_id: uuid.UUID
) -> bool:
    response = client.get(
        f"{settings.API_V1_STR}/items/{item_id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    return response.json()["archived"]


def test_new_item_is_not_archived(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json={"title": "Foo", "description": "Fighters"},
    )
    assert response.status_code == 200
    assert response.json()["archived"] is False


def test_archive_own_item(client: TestClient, db: Session) -> None:
    user_id, headers = _create_user_with_headers(client, db)
    item = _create_item(db, user_id)

    response = _archive(client, headers, item.id)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(item.id)
    assert content["title"] == item.title
    assert content["owner_id"] == str(user_id)
    assert content["archived"] is True

    response = client.get(f"{settings.API_V1_STR}/items/{item.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["archived"] is True


def test_archive_already_archived_item_is_idempotent(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _create_user_with_headers(client, db)
    item = _create_item(db, user_id)

    assert _archive(client, headers, item.id).status_code == 200
    response = _archive(client, headers, item.id)
    assert response.status_code == 200
    assert response.json()["archived"] is True


def test_unarchive_own_item_returns_to_default_list(
    client: TestClient, db: Session
) -> None:
    user_id, headers = _create_user_with_headers(client, db)
    item = _create_item(db, user_id)
    assert _archive(client, headers, item.id).status_code == 200

    response = _unarchive(client, headers, item.id)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(item.id)
    assert content["archived"] is False

    response = client.get(f"{settings.API_V1_STR}/items/", headers=headers)
    assert response.status_code == 200
    ids = [i["id"] for i in response.json()["data"]]
    assert str(item.id) in ids


def test_unarchive_active_item_is_idempotent(client: TestClient, db: Session) -> None:
    user_id, headers = _create_user_with_headers(client, db)
    item = _create_item(db, user_id)

    response = _unarchive(client, headers, item.id)
    assert response.status_code == 200
    assert response.json()["archived"] is False


def test_read_items_hides_archived_by_default(client: TestClient, db: Session) -> None:
    user_id, headers = _create_user_with_headers(client, db)
    active_1 = _create_item(db, user_id)
    active_2 = _create_item(db, user_id)
    archived = _create_item(db, user_id)
    assert _archive(client, headers, archived.id).status_code == 200

    response = client.get(f"{settings.API_V1_STR}/items/", headers=headers)
    assert response.status_code == 200
    content = response.json()
    ids = {i["id"] for i in content["data"]}
    assert ids == {str(active_1.id), str(active_2.id)}
    assert content["count"] == 2
    assert all(i["archived"] is False for i in content["data"])


def test_read_items_superuser_hides_archived_by_default(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    active = create_random_item(db)
    archived = create_random_item(db)
    assert _archive(client, superuser_token_headers, archived.id).status_code == 200

    response = client.get(
        f"{settings.API_V1_STR}/items/", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    ids = [i["id"] for i in content["data"]]
    assert str(active.id) in ids
    assert str(archived.id) not in ids
    assert all(i["archived"] is False for i in content["data"])

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        params={"include_archived": "true"},
    )
    assert response.status_code == 200
    ids = [i["id"] for i in response.json()["data"]]
    assert str(archived.id) in ids


def test_read_items_include_archived(client: TestClient, db: Session) -> None:
    user_id, headers = _create_user_with_headers(client, db)
    active = _create_item(db, user_id)
    archived = _create_item(db, user_id)
    assert _archive(client, headers, archived.id).status_code == 200

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        params={"include_archived": "true"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2
    by_id = {i["id"]: i for i in content["data"]}
    assert set(by_id) == {str(active.id), str(archived.id)}
    assert by_id[str(active.id)]["archived"] is False
    assert by_id[str(archived.id)]["archived"] is True


def test_read_items_include_archived_invalid_value(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        params={"include_archived": "notabool"},
    )
    assert response.status_code == 422


def test_archive_not_owner_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    item = create_random_item(db)

    response = _archive(client, normal_user_token_headers, item.id)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"
    assert _get_archived(client, superuser_token_headers, item.id) is False


def test_unarchive_not_owner_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    owner_id, owner_headers = _create_user_with_headers(client, db)
    item = _create_item(db, owner_id)
    assert _archive(client, owner_headers, item.id).status_code == 200

    response = _unarchive(client, normal_user_token_headers, item.id)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"
    assert _get_archived(client, superuser_token_headers, item.id) is True


def test_superuser_can_archive_and_unarchive_any_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)

    response = _archive(client, superuser_token_headers, item.id)
    assert response.status_code == 200
    assert response.json()["archived"] is True
    assert response.json()["owner_id"] == str(item.owner_id)
    assert _get_archived(client, superuser_token_headers, item.id) is True

    response = _unarchive(client, superuser_token_headers, item.id)
    assert response.status_code == 200
    assert response.json()["archived"] is False
    assert _get_archived(client, superuser_token_headers, item.id) is False


def test_archive_unarchive_unauthenticated(client: TestClient, db: Session) -> None:
    item = create_random_item(db)
    for path in ("archive", "unarchive"):
        response = client.patch(f"{settings.API_V1_STR}/items/{item.id}/{path}")
        assert response.status_code in (401, 403)


def test_archive_unarchive_invalid_token(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    headers = {"Authorization": "Bearer invalid-token"}
    for path in ("archive", "unarchive"):
        response = client.patch(
            f"{settings.API_V1_STR}/items/{item.id}/{path}", headers=headers
        )
        assert response.status_code in (401, 403)
    assert _get_archived(client, superuser_token_headers, item.id) is False


def test_archive_unarchive_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    for path in ("archive", "unarchive"):
        response = client.patch(
            f"{settings.API_V1_STR}/items/{uuid.uuid4()}/{path}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Item not found"


def test_count_still_includes_archived_items(client: TestClient, db: Session) -> None:
    user_id, headers = _create_user_with_headers(client, db)
    _create_item(db, user_id)
    archived = _create_item(db, user_id)
    assert _archive(client, headers, archived.id).status_code == 200

    response = client.get(f"{settings.API_V1_STR}/items/count", headers=headers)
    assert response.status_code == 200
    assert response.json() == 2
