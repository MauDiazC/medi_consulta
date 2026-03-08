from fastapi import APIRouter, Depends

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
async def create_user(payload: UserCreate, s=Depends(get_service)):
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
    await s.deactivate(user_id, user["org"])
    return {"status": "deactivated"}