import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.modules.auth.service import AuthService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_repo):
    return AuthService(repo=mock_repo)


async def test_login_success(auth_service, mock_repo):
    # Setup
    mock_user = {
        "id": "user_id_123",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "role": "admin",
        "organization_id": "org_id_123"
    }
    mock_repo.get_user_by_email.return_value = mock_user

    with patch("app.modules.auth.service.verify_password", return_value=True), \
         patch("app.modules.auth.service.create_access_token", return_value="fake_token"):
        
        # Execute
        token = await auth_service.login("test@example.com", "password123")

        # Verify
        assert token == "fake_token"
        mock_repo.get_user_by_email.assert_called_once_with("test@example.com")


async def test_login_invalid_email(auth_service, mock_repo):
    # Setup
    mock_repo.get_user_by_email.return_value = None

    # Execute & Verify
    with pytest.raises(HTTPException) as exc:
        await auth_service.login("nonexistent@example.com", "password123")
    
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


async def test_login_invalid_password(auth_service, mock_repo):
    # Setup
    mock_user = {
        "id": "user_id_123",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "role": "admin",
        "organization_id": "org_id_123"
    }
    mock_repo.get_user_by_email.return_value = mock_user

    with patch("app.modules.auth.service.verify_password", return_value=False):
        # Execute & Verify
        with pytest.raises(HTTPException) as exc:
            await auth_service.login("test@example.com", "wrong_password")
        
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid credentials"


async def test_exchange_success(auth_service, mock_repo):
    # Setup
    mock_repo.get_user_by_id.return_value = {
        "id": "user_id_123",
        "role": "admin",
        "organization_id": "org_id_123"
    }

    with patch("app.modules.auth.service.verify_supabase_token", return_value={"sub": "user_id_123"}), \
         patch("app.modules.auth.service.create_access_token", return_value="fake_token"):
        
        # Execute
        token = await auth_service.exchange("supabase_token_123")

        # Verify
        assert token == "fake_token"
        mock_repo.get_user_by_id.assert_called_once_with("user_id_123")


async def test_exchange_user_not_found(auth_service, mock_repo):
    # Setup
    mock_repo.get_user_by_id.return_value = None

    with patch("app.modules.auth.service.verify_supabase_token", return_value={"sub": "user_id_123"}):
        # Execute & Verify
        with pytest.raises(HTTPException) as exc:
            await auth_service.exchange("supabase_token_123")
        
        assert exc.value.status_code == 403
        assert exc.value.detail == "User identity verified but not onboarded in Mediconsulta."


async def test_bootstrap_new_user(auth_service, mock_repo):
    # Setup
    mock_identity = {"id": "new_user_id", "email": "new@example.com", "full_name": "New User"}
    mock_repo.get_user_by_id.return_value = None
    mock_repo.bootstrap_user.return_value = {
        "id": "new_user_id",
        "role": "admin",
        "organization_id": None
    }

    with patch("app.modules.auth.service.verify_supabase_token", return_value={"sub": "new_user_id"}), \
         patch("app.modules.auth.service.normalize_supabase_identity", return_value=mock_identity), \
         patch("app.modules.auth.service.create_access_token", return_value="bootstrap_token"):
        
        # Execute
        token = await auth_service.bootstrap("supabase_token_123")

        # Verify
        assert token == "bootstrap_token"
        mock_repo.bootstrap_user.assert_called_once()


async def test_exchange_identity_failure(auth_service):
    with patch("app.modules.auth.service.verify_supabase_token", side_effect=Exception("Invalid token")):
        with pytest.raises(HTTPException) as exc:
            await auth_service.exchange("bad_token")
        
        assert exc.value.status_code == 401
        assert "Identity verification failed" in exc.value.detail


async def test_bootstrap_identity_failure(auth_service):
    with patch("app.modules.auth.service.verify_supabase_token", side_effect=Exception("Invalid token")):
        with pytest.raises(HTTPException) as exc:
            await auth_service.bootstrap("bad_token")
        
        assert exc.value.status_code == 401
        assert "Identity verification failed" in exc.value.detail
