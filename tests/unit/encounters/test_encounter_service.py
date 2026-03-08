import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from app.modules.encounters.service import EncounterService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def encounter_service(mock_repo):
    return EncounterService(repo=mock_repo)


async def test_create_encounter(encounter_service, mock_repo):
    # Setup
    mock_payload = AsyncMock(clinical_session_id=1, patient_id=1, reason="Checkup")
    mock_repo.create.return_value = {"id": 1, "status": "open"}

    # Execute
    encounter = await encounter_service.create(mock_payload, "org_123", "doctor_123")

    # Verify
    assert encounter["id"] == 1
    mock_repo.create.assert_called_once_with(mock_payload, "org_123", "doctor_123")


async def test_get_encounter_success(encounter_service, mock_repo):
    # Setup
    mock_repo.get.return_value = {"id": 1, "status": "open"}

    # Execute
    encounter = await encounter_service.get(1, "org_123")

    # Verify
    assert encounter["id"] == 1
    mock_repo.get.assert_called_once_with(1, "org_123")


async def test_get_encounter_not_found(encounter_service, mock_repo):
    # Setup
    mock_repo.get.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc:
        await encounter_service.get(99, "org_123")
    
    assert exc.value.status_code == 404


async def test_list_encounters(encounter_service, mock_repo):
    # Setup
    mock_repo.list.return_value = [{"id": 1}, {"id": 2}]

    # Execute
    encounters = await encounter_service.list("org_123", 10, 0)

    # Verify
    assert len(encounters) == 2
    mock_repo.list.assert_called_once_with("org_123", 10, 0)


async def test_list_by_patient(encounter_service, mock_repo):
    # Setup
    mock_repo.list_by_patient.return_value = [{"id": 1}]

    # Execute
    encounters = await encounter_service.list_by_patient(1, "org_123", 10, 0)

    # Verify
    assert len(encounters) == 1
    mock_repo.list_by_patient.assert_called_once_with(1, "org_123", 10, 0)


async def test_list_by_doctor(encounter_service, mock_repo):
    # Setup
    mock_repo.list_by_doctor.return_value = [{"id": 1}]

    # Execute
    encounters = await encounter_service.list_by_doctor("doctor_123", "org_123", 10, 0)

    # Verify
    assert len(encounters) == 1
    mock_repo.list_by_doctor.assert_called_once_with("doctor_123", "org_123", 10, 0)


async def test_list_by_session(encounter_service, mock_repo):
    # Setup
    mock_repo.list_by_session.return_value = [{"id": 1}]

    # Execute
    encounters = await encounter_service.list_by_session(1, "org_123", 10, 0)

    # Verify
    assert len(encounters) == 1
    mock_repo.list_by_session.assert_called_once_with(1, "org_123", 10, 0)


async def test_update_encounter_success(encounter_service, mock_repo):
    # Setup
    mock_payload = AsyncMock(reason="Urgent Checkup")
    mock_repo.update.return_value = {"id": 1, "reason": "Urgent Checkup"}

    # Execute
    encounter = await encounter_service.update(1, "org_123", mock_payload)

    # Verify
    assert encounter["reason"] == "Urgent Checkup"


async def test_update_encounter_not_found(encounter_service, mock_repo):
    # Setup
    mock_repo.update.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc:
        await encounter_service.update(99, "org_123", AsyncMock())
    
    assert exc.value.status_code == 404


async def test_close_encounter(encounter_service, mock_repo):
    # Execute
    await encounter_service.close(1, "org_123")

    # Verify
    mock_repo.close.assert_called_once_with(1, "org_123")
