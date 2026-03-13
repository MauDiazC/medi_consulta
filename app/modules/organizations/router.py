from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import pagination_params
from app.modules.users.repository import UserRepository

from .repository import OrganizationRepository
from .schemas import OrganizationCreate, OrganizationUpdate
from .service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_service(db=Depends(get_db)):
    return OrganizationService(
        OrganizationRepository(db),
        UserRepository(db)
    )


@router.post("")
async def create_org(
    payload: OrganizationCreate, 
    user=Depends(get_current_user),
    s=Depends(get_service)
):
    return await s.create(payload, user["sub"])


@router.get("")
async def list_orgs(page=Depends(pagination_params), s=Depends(get_service)):
    return await s.list(page.limit, page.offset)


@router.get("/{org_id}")
async def get_org(org_id: str, s=Depends(get_service)):
    return await s.get(org_id)


@router.put("/{org_id}")
async def update_org(
    org_id: str,
    payload: OrganizationUpdate,
    s=Depends(get_service),
):
    return await s.update(org_id, payload)


@router.patch("/{org_id}/deactivate")
async def deactivate_org(org_id: str, s=Depends(get_service)):
    await s.deactivate(org_id)
    return {"status": "deactivated"}
