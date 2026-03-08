import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.modules.users.service import UserService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def user_service(mock_repo):
    return UserService(repo=mock_repo)


async def test_create_user(user_service, mock_repo):
    mock_payload = AsyncMock(email="test@example.com", password="pass", role="admin", organization_id="org1")
    mock_repo.create.return_value = {"id": "u1"}
    
    with patch("app.modules.users.service.hash_password", return_value="hashed"):
        user = await user_service.create(mock_payload)
        assert user["id"] == "u1"
        mock_repo.create.assert_called_once_with("test@example.com", "hashed", "admin", "org1")


async def test_get_user_success(user_service, mock_repo):
    mock_repo.get.return_value = {"id": "u1"}
    user = await user_service.get("u1", "org1")
    assert user["id"] == "u1"


async def test_get_user_not_found(user_service, mock_repo):
    mock_repo.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await user_service.get("u1", "org1")
    assert exc.value.status_code == 404


async def test_list_users(user_service, mock_repo):
    mock_repo.list.return_value = [{"id": "u1"}]
    users = await user_service.list("org1", 10, 0)
    assert len(users) == 1


async def test_update_user_success(user_service, mock_repo):
    mock_payload = AsyncMock()
    mock_repo.update.return_value = {"id": "u1"}
    user = await user_service.update("u1", "org1", mock_payload)
    assert user["id"] == "u1"


async def test_update_user_not_found(user_service, mock_repo):
    mock_repo.update.return_value = None
    with pytest.raises(HTTPException) as exc:
        await user_service.update("u1", "org1", AsyncMock())
    assert exc.value.status_code == 404


async def test_deactivate_user(user_service, mock_repo):
    await user_service.deactivate("u1", "org1")
    mock_repo.deactivate.assert_called_once_with("u1", "org1")
