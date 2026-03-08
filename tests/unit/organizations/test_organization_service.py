import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.modules.organizations.service import OrganizationService


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.db = MagicMock()
    # Properly mock async context manager for db.begin()
    mock_begin = MagicMock()
    mock_begin.__aenter__ = AsyncMock()
    mock_begin.__aexit__ = AsyncMock(return_value=False) # Do NOT suppress exceptions
    repo.db.begin.return_value = mock_begin
    
    repo.create = AsyncMock()
    repo.get = AsyncMock()
    repo.list = AsyncMock()
    repo.update = AsyncMock()
    repo.deactivate = AsyncMock()
    
    return repo


@pytest.fixture
def mock_user_repo():
    user_repo = MagicMock()
    user_repo.assign_organization = AsyncMock()
    return user_repo


@pytest.fixture
def organization_service(mock_repo, mock_user_repo):
    return OrganizationService(repo=mock_repo, user_repo=mock_user_repo)


async def test_create_organization(organization_service, mock_repo, mock_user_repo):
    # Setup
    mock_payload = MagicMock()
    mock_payload.name = "Clinic Alpha"
    mock_repo.create.return_value = {"id": "org_1", "name": "Clinic Alpha"}
    
    # Execute
    org = await organization_service.create(mock_payload, "user_123")
    
    # Verify
    assert org["id"] == "org_1"
    mock_repo.create.assert_called_once_with("Clinic Alpha")
    mock_user_repo.assign_organization.assert_called_once_with("user_123", "org_1")


async def test_get_organization_success(organization_service, mock_repo):
    mock_repo.get.return_value = {"id": "org_1"}
    org = await organization_service.get("org_1")
    assert org["id"] == "org_1"


async def test_get_organization_not_found(organization_service, mock_repo):
    mock_repo.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await organization_service.get("invalid")
    assert exc.value.status_code == 404


async def test_list_organizations(organization_service, mock_repo):
    mock_repo.list.return_value = [{"id": "org_1"}]
    orgs = await organization_service.list(10, 0)
    assert len(orgs) == 1


async def test_update_organization_success(organization_service, mock_repo):
    mock_payload = MagicMock()
    mock_repo.update.return_value = {"id": "org_1"}
    org = await organization_service.update("org_1", mock_payload)
    assert org["id"] == "org_1"


async def test_update_organization_not_found(organization_service, mock_repo):
    mock_repo.update.return_value = None
    with pytest.raises(HTTPException) as exc:
        await organization_service.update("org_1", MagicMock())
    assert exc.value.status_code == 404


async def test_deactivate_organization(organization_service, mock_repo):
    await organization_service.deactivate("org_1")
    mock_repo.deactivate.assert_called_once_with("org_1")
