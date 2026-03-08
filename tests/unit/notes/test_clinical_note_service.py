import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.modules.notes.service import ClinicalNoteService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.db = AsyncMock()  # Mock for self.repo.db
    return repo


@pytest.fixture
def note_service(mock_repo):
    return ClinicalNoteService(repo=mock_repo)


async def test_autosave_success(note_service, mock_repo):
    # Setup
    encounter_id = "enc_123"
    doctor_id = "doc_123"
    fields = {"subjective": "Patient feels better"}
    expected_at = "2023-01-01T00:00:00"
    
    mock_repo.get_active_draft.return_value = {
        "id": "note_1",
        "created_by": doctor_id,
        "version": 1
    }
    mock_repo.autosave_update.return_value = {"id": "note_1", **fields}

    with patch("app.modules.notes.service.publish_event", AsyncMock()), \
         patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False):
        
        # Execute
        result = await note_service.autosave(encounter_id, doctor_id, fields, expected_at)

        # Verify
        assert result["id"] == "note_1"
        mock_repo.autosave_update.assert_called_once()


async def test_autosave_sealed_encounter(note_service, mock_repo):
    # Setup
    encounter_id = "enc_sealed"
    
    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=True):
        # Execute & Verify
        with pytest.raises(HTTPException) as exc:
            await note_service.autosave(encounter_id, "doc_123", {}, "at")
        
        assert exc.value.status_code == 400
        assert "sealed" in exc.value.detail


async def test_autosave_draft_not_found(note_service, mock_repo):
    mock_repo.get_active_draft.return_value = None
    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await note_service.autosave("enc_123", "doc_123", {}, "at")
        assert exc.value.status_code == 404


async def test_autosave_conflict(note_service, mock_repo):
    mock_repo.get_active_draft.return_value = {"id": "n1", "created_by": "doc_123"}
    mock_repo.autosave_update.return_value = None
    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await note_service.autosave("enc_123", "doc_123", {}, "at")
        assert exc.value.status_code == 409


async def test_autosave_unauthorized(note_service, mock_repo):
    # Setup
    mock_repo.get_active_draft.return_value = {
        "id": "note_1",
        "created_by": "other_doctor",
        "version": 1
    }

    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False):
        # Execute & Verify
        with pytest.raises(HTTPException) as exc:
            await note_service.autosave("enc_123", "doc_123", {}, "at")
        
        assert exc.value.status_code == 403


async def test_finalize_version_success(note_service, mock_repo):
    # Setup
    encounter_id = "enc_123"
    doctor_id = "doc_123"
    mock_repo.get_active_draft.return_value = {
        "id": "note_v1",
        "version": 1,
        "subjective": "S", "objective": "O", "assessment": "A", "plan": "P"
    }
    mock_repo.create_new_version.return_value = {"id": "note_v2", "version": 2}

    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False), \
         patch("app.modules.notes.service.audit_log", AsyncMock()):
        
        # Execute
        new_note = await note_service.finalize_version(encounter_id, doctor_id)

        # Verify
        assert new_note["version"] == 2
        mock_repo.deactivate_draft.assert_called_once_with("note_v1")
        mock_repo.create_new_version.assert_called_once()


async def test_finalize_version_no_draft(note_service, mock_repo):
    mock_repo.get_active_draft.return_value = None
    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await note_service.finalize_version("enc_123", "doc_123")
        assert exc.value.status_code == 404


async def test_sign_success(note_service, mock_repo):
    note_id = "note_1"
    doctor_id = "doc_123"
    mock_note = {"id": note_id, "created_by": doctor_id, "encounter_id": "enc_1", "signed_at": None}
    mock_repo.get_note_and_version.return_value = (mock_note, {"v": 1})
    
    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False), \
         patch("app.modules.notes.signing.service.SigningApplicationService.execute_signing", AsyncMock()) as mock_exec, \
         patch("app.modules.notes.service.publish_event", AsyncMock()):
        
        res = await note_service.sign(note_id, doctor_id)
        assert res["signed"] is True
        mock_exec.assert_called_once()


async def test_sign_not_found(note_service, mock_repo):
    mock_repo.get_note_and_version.return_value = (None, None)
    with pytest.raises(HTTPException) as exc:
        await note_service.sign("n1", "d1")
    assert exc.value.status_code == 404


async def test_sign_already_signed(note_service, mock_repo):
    mock_repo.get_note_and_version.return_value = ({"signed_at": "now", "encounter_id": "e1"}, {})
    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await note_service.sign("n1", "d1")
        assert exc.value.status_code == 400


async def test_sign_unauthorized(note_service, mock_repo):
    # Setup
    mock_repo.get_note_and_version.return_value = (
        {"id": "note_1", "created_by": "other_doc", "encounter_id": "enc_123", "signed_at": None},
        {"version": 1}
    )

    with patch("app.modules.notes.signing.repository.SigningRepository.is_encounter_sealed", return_value=False):
        # Execute & Verify
        with pytest.raises(HTTPException) as exc:
            await note_service.sign("note_1", "doc_123")
        
        assert exc.value.status_code == 403


async def test_diff_versions_success(note_service, mock_repo):
    # Setup
    mock_repo.get_version.side_effect = [
        {"subjective": "old content"},
        {"subjective": "new content"}
    ]

    with patch("app.modules.notes.service.build_diff", return_value={"diff": "..."}):
        # Execute
        diff = await note_service.diff_versions("enc_123", 1, 2)

        # Verify
        assert diff == {"diff": "..."}
        assert mock_repo.get_version.call_count == 2


async def test_diff_versions_not_found(note_service, mock_repo):
    mock_repo.get_version.return_value = None
    with pytest.raises(HTTPException) as exc:
        await note_service.diff_versions("e1", 1, 2)
    assert exc.value.status_code == 404
