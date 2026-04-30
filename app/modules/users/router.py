from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import pagination_params
from app.core.permissions import require_role

from .repository import UserRepository
from .schemas import UserCreate, UserUpdate
from .service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_service(db=Depends(get_db)):
    return UserService(UserRepository(db))


@router.post("")
async def create_user(
    payload: UserCreate, 
    user=Depends(require_role("admin")),
    s=Depends(get_service)
):
    """
    Creates a new user. 
    SaaS Guard: Only admins can create users, and they must be in their org.
    """
    if str(payload.organization_id) != str(user["org"]):
        raise HTTPException(status_code=403, detail="Cannot create user for another organization")
        
    return await s.create(payload)


@router.get("")
async def list_users(
    page=Depends(pagination_params),
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.list(user["org"], page.limit, page.offset)


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    user=Depends(get_current_user),
    s=Depends(get_service),
):
    return await s.get(user_id, user["org"])


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    payload: UserUpdate,
    user=Depends(require_role("admin")),
    s=Depends(get_service),
):
    return await s.update(user_id, user["org"], payload)


@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    user=Depends(require_role("admin")),
    s=Depends(get_service),
):
    """Soft delete: Marks the user as inactive."""
    return await s.deactivate(user_id, user["org"])


@router.patch("/{user_id}/activate")
async def activate_user(
    user_id: str,
    user=Depends(require_role("admin")),
    s=Depends(get_service),
):
    """Re-enables an inactive user."""
    return await s.activate(user_id, user["org"])


@router.delete("/{user_id}/purge")
async def hard_delete_user(
    user_id: str,
    user=Depends(require_role("admin")),
    s=Depends(get_service),
):
    """
    DANGER: Physical deletion of a user.
    TEMPORARY: Only for development testing.
    """
    # Use the email from the user record to call repo purge
    target_user = await s.get(user_id, user["org"])
    await s.repo.hard_delete_by_email(target_user["email"])
    return {"status": "purged", "email": target_user["email"]}

# --- Staff Assignments ---

@router.post("/{staff_id}/assignments/{doctor_id}")
async def assign_doctor(
    staff_id: str,
    doctor_id: str,
    user=Depends(require_role("admin")),
    s=Depends(get_service)
):
    """Assigns a doctor to a staff member (assistant, nurse, admin)."""
    return await s.assign_doctor(staff_id, doctor_id, user["org"])

@router.delete("/{staff_id}/assignments/{doctor_id}")
async def remove_assignment(
    staff_id: str,
    doctor_id: str,
    user=Depends(require_role("admin")),
    s=Depends(get_service)
):
    """Removes a doctor assignment from a staff member."""
    return await s.remove_assignment(staff_id, doctor_id, user["org"])

@router.get("/{staff_id}/assignments")
async def list_assignments(
    staff_id: str,
    user=Depends(require_role("admin")),
    s=Depends(get_service)
):
    """Lists all doctors assigned to a staff member."""
    return await s.get_assigned_doctors(staff_id, user["org"])
