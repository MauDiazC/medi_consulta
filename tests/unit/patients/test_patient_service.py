import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from app.modules.patients.service import PatientService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def patient_service(mock_repo):
    return PatientService(repo=mock_repo)


async def test_create_patient(patient_service, mock_repo):
    # Setup
    mock_payload = AsyncMock(first_name="John", last_name="Doe")
    mock_repo.create.return_value = {"id": 1, "first_name": "John", "last_name": "Doe"}

    # Execute
    patient = await patient_service.create(mock_payload, "org_123")

    # Verify
    assert patient["id"] == 1
    mock_repo.create.assert_called_once_with(mock_payload, "org_123")


async def test_get_patient_success(patient_service, mock_repo):
    # Setup
    mock_repo.get.return_value = {"id": 1, "first_name": "John", "last_name": "Doe"}

    # Execute
    patient = await patient_service.get(1, "org_123")

    # Verify
    assert patient["id"] == 1
    mock_repo.get.assert_called_once_with(1, "org_123")


async def test_get_patient_not_found(patient_service, mock_repo):
    # Setup
    mock_repo.get.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc:
        await patient_service.get(99, "org_123")
    
    assert exc.value.status_code == 404


async def test_update_patient_success(patient_service, mock_repo):
    # Setup
    mock_payload = AsyncMock(first_name="Jane", last_name="Doe")
    mock_repo.update.return_value = {"id": 1, "first_name": "Jane", "last_name": "Doe"}

    # Execute
    patient = await patient_service.update(1, "org_123", mock_payload)

    # Verify
    assert patient["first_name"] == "Jane"


async def test_update_patient_not_found(patient_service, mock_repo):
    # Setup
    mock_repo.update.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc:
        await patient_service.update(99, "org_123", AsyncMock())
    
    assert exc.value.status_code == 404


async def test_list_patients(patient_service, mock_repo):
    # Setup
    mock_repo.list.return_value = [{"id": 1}, {"id": 2}]

    # Execute
    patients = await patient_service.list("org_123", 10, 0)

    # Verify
    assert len(patients) == 2
    mock_repo.list.assert_called_once_with("org_123", 10, 0)


async def test_deactivate_patient(patient_service, mock_repo):
    # Execute
    await patient_service.deactivate(1, "org_123")

    # Verify
    mock_repo.deactivate.assert_called_once_with(1, "org_123")
